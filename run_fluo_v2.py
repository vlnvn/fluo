#!/usr/bin/env python3
"""FLUO P1 v2: synthetic-only deficit signature detection & evidence-first P2 core.
Train supervised on v1 TRAIN simulation labels as TARGETS ONLY.
Choose fixed score threshold using development seeds; locked set read only after decision frozen.
No valve actuation, fault localization, calibrated probabilities, or claims of real-world efficacy.
"""
import argparse,json,hashlib,platform
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from joblib import dump
from importlib.metadata import version
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_fluo_ml_v1 import build_features

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'data'/'original'
FEATURES=['loss_ratio_instant','loss_ratio_ewma5','loss_ratio_ewma15','steam_step_rel','steam_rolling_cv','return_rolling_cv']
THRESHOLDS={'fixed_ratio':.15,'physics_residual':.09,'gb_signature':.90}
WINDOW=10;K=5;WARMUP=20;RECONNECT=5;SEED=71
POSITIVE=('diversion_to_pit','return_pipe_loss','trap_blowthrough','return_meter_bias')

def fmt_data(sensor):
    # No file containing ground-truth is read by this function.
    d=build_features(sensor)
    d['position_in_mode']=d.groupby(['site_id',(d['operating_mode'].ne(d['operating_mode'].shift())).cumsum()]).cumcount()
    good=d.gate_valid & (d.position_in_mode>=WARMUP)
    # inhibit alarms immediately after a period of offline/missing/invalid telemetry.
    d['run_good']=good.groupby(d.site_id).transform(lambda x:x.astype(int).groupby((~x).cumsum()).cumsum())
    d['decision_valid']=good & (d.run_good>=RECONNECT)
    return d

def train_model():
    s=pd.read_csv(SOURCE/'fluo_sensor_stream.csv.gz')
    truth=pd.read_csv(SOURCE/'fluo_physics_ground_truth.csv.gz',usecols=['site_id','minute_id','event_type'])
    d=fmt_data(s)
    # Target join ONLY for training labels. NEVER added to X.
    y=d[['site_id','minute_id','split']].merge(truth,on=['site_id','minute_id'],validate='one_to_one').event_type.isin(POSITIVE)
    mask=d.split.eq('train') & d.decision_valid
    X=d.loc[mask,FEATURES].astype(float)
    target=y.loc[mask].astype(int)
    assert not any(c in X.columns for c in ['site_id','minute_id','split','event_type','event_group','event_id'])
    model=HistGradientBoostingClassifier(max_iter=75,max_leaf_nodes=9,min_samples_leaf=70,l2_regularization=3.,learning_rate=.05,random_state=SEED)
    model.fit(X,target)
    return model,{'n_train':len(X),'n_positive_train':int(target.sum()),'fit_target':'synthetic physical loss OR observed return-meter bias, NOT verified causal diagnosis','input_features':FEATURES}

def inference(sensor,model,run_mode='SYNTHETIC_REPLAY'):
    """Synthetic replay ONLY. Fail closed for real-world mode and schema errors."""
    if run_mode != 'SYNTHETIC_REPLAY':
        raise RuntimeError('FIELD DEPLOYMENT DENIED: needs independent calibration, safety review, validated sensors and authorized commissioning')
    required={'timestamp','site_id','minute_id','split','operating_mode','throughput_index','steam_flow_obs_kg_h','condensate_return_obs_kg_h','steam_pressure_obs_barg','steam_temperature_obs_C','return_temperature_obs_C','link_online','data_quality_flag'}
    if not required.issubset(sensor.columns):
        raise ValueError(f'Missing required telemetry fields: {sorted(required-set(sensor.columns))}')
    if sensor.duplicated(['site_id','minute_id']).any():
        raise ValueError('Duplicate site_id/minute_id')
    if (sensor[['steam_flow_obs_kg_h','condensate_return_obs_kg_h']].lt(0)).any().any():
        raise ValueError('Impossible negative mass-flow: reject input')
    if not sensor.link_online.isin([0,1]).all():
        raise ValueError('link_online must be 0/1')
    d=fmt_data(sensor)
    valid=d.decision_valid.to_numpy()
    output=d[['site_id','timestamp','minute_id','split','operating_mode','link_online','data_quality_flag','steam_flow_obs_kg_h','condensate_return_obs_kg_h','steam_pressure_obs_barg','return_temperature_obs_C']].copy()
    scores={'fixed_ratio': 1.-d['condensate_return_obs_kg_h'].to_numpy(float)/np.maximum(d['steam_flow_obs_kg_h'].to_numpy(float),8.),
            'physics_residual':d['loss_ratio_ewma5'].to_numpy(float),
            'gb_signature':np.full(len(d),np.nan,dtype=float)}
    scores['gb_signature'][valid]=model.predict_proba(d.loc[valid,FEATURES].astype(float))[:,1]
    for method,score in scores.items():
        output[f'{method}_score']=score
        candidate=(score>THRESHOLDS[method]) & valid & np.isfinite(score)
        # reset persistence after invalid samples, do not generate alarm on bad quality
        persistent=pd.Series(candidate,index=d.index).groupby(d.site_id).transform(lambda x:x.rolling(WINDOW,min_periods=WINDOW).sum().ge(K)).to_numpy() & valid
        output[f'{method}_warning']=persistent
    output['quality_action']=np.select([
        d.link_online.eq(0).to_numpy(),
        d.condensate_return_obs_kg_h.isna().to_numpy(),
        d.operating_mode.ne('production').to_numpy(),
        d.position_in_mode.lt(WARMUP).to_numpy(),
        ~valid],['GATEWAY_OFFLINE','VERIFY_RETURN_METER','NONPRODUCTION_MONITORING_ONLY','MODE_STABILIZATION','INSUFFICIENT_VALID_HISTORY'],default='SCORE_ALLOWED')
    output['triage_status']=np.where(output['quality_action']!='SCORE_ALLOWED','DATA_OR_MODE_CHECK',
                                     np.where(output['gb_signature_warning'],'INVESTIGATE_RETURN_DEFICIT_UNCONFIRMED','MONITOR'))
    output['next_safe_action']=np.where(output['triage_status']=='INVESTIGATE_RETURN_DEFICIT_UNCONFIRMED',
                                       'Verify time alignment and steam/return meters; confirm process mode; inspect drain/return and steam trap with authorized technician; assess condensate quality before recovery',
                                       np.where(output['quality_action']=='SCORE_ALLOWED','Continue read-only monitoring','Review quality/mode status; do not infer physical loss'))
    output['recovery_eligibility']='UNKNOWN_REQUIRES_SITE_ASSESSMENT'
    output['auto_actuation_allowed']=False
    output['score_meaning']='uncalibrated synthetic signature score, not physical-loss probability'
    return output

def evaluate(pred,folder,phase,seed):
    truth=pd.read_csv(folder/'fluo_physics_ground_truth.csv.gz',usecols=['site_id','minute_id','event_id','event_group','event_type'])
    eps=pd.read_csv(folder/'fluo_episode_labels.csv')
    d=pred.merge(truth,on=['site_id','minute_id'],validate='one_to_one')
    d['timestamp_dt']=pd.to_datetime(d['timestamp'],utc=True)
    d['is_event']=d.event_id.notna() & d.event_id.ne('')
    # buffer around all events for conservative baseline background nuisance accounting
    eventnear=np.zeros(len(d),bool)
    for _,g in d.groupby('site_id',sort=False):
        ix=g.index.to_numpy()
        ev=g.is_event.to_numpy()
        eventnear[ix]=(pd.Series(ev).rolling(91,center=True,min_periods=1).max().to_numpy()>0)
    d['isolated_clean']=~eventnear & d.quality_action.eq('SCORE_ALLOWED')
    rows=[];erows=[]
    for method in THRESHOLDS:
        warning=f'{method}_warning'
        for ep in eps.itertuples(index=False):
            st=pd.Timestamp(ep.start_timestamp).tz_convert('UTC');en=pd.Timestamp(ep.end_timestamp_inclusive).tz_convert('UTC')
            g=d[(d.site_id==ep.site_id)&d.timestamp_dt.between(st,en)]
            a=g[g[warning]]
            delay=int((a.iloc[0].timestamp_dt-st).total_seconds()/60) if len(a) else None
            erows.append({'phase':phase,'seed':seed,'method':method,'site_id':ep.site_id,'event_id':ep.event_id,'event_group':ep.event_group,'event_type':ep.event_type,'duration_min':int(ep.duration_min),'detected':len(a)>0,'first_warning_delay_min':delay})
        er=pd.DataFrame(erows)
        m=er[(er.method==method)&(er.phase==phase)&(er.seed==seed)]
        phys=m[m.event_group=='physical_loss'];bias=m[m.event_type=='return_meter_bias'];delay=m[m.event_type=='transport_delay_shift']
        miss=m[m.event_type=='return_meter_dropout'];off=m[m.event_type=='network_outage']
        # Count starts in clean windows; cooldown assessed by minute id gaps 30min
        noevent=d[d.isolated_clean]
        starts=0
        for _,g in noevent.groupby('site_id'):
            mins=g.loc[g[warning],'minute_id'].to_numpy()
            if len(mins): starts+=int(1+(np.diff(mins)>30).sum())
        hour=len(noevent)/60
        nonloss=m[m.event_group!='physical_loss']
        rows.append(dict(phase=phase,seed=seed,method=method,
            physical_detected=int(phys.detected.sum()),physical_total=len(phys),
            sensor_bias_warned=int(bias.detected.sum()),sensor_bias_total=len(bias),
            transport_delay_warned=int(delay.detected.sum()),transport_delay_total=len(delay),
            dropout_warned=int(miss.detected.sum()),dropout_total=len(miss),
            offline_warned=int(off.detected.sum()),offline_total=len(off),
            nonphysical_episode_warned=int(nonloss.detected.sum()),nonphysical_total=len(nonloss),
            clean_false_clusters=starts,clean_hours=hour,
            clean_clusters_per_100h=round(starts*100/hour,4) if hour>0 else None,
            median_detection_delay_min=phys.loc[phys.detected,'first_warning_delay_min'].median() if phys.detected.any() else None,
            scoreable_minutes=int(d.quality_action.eq('SCORE_ALLOWED').sum()),
            total_minutes=len(d),warning_minutes=int(d[warning].sum())))
    return pd.DataFrame(rows),pd.DataFrame(erows)

def main():
    ROOT.mkdir(exist_ok=True,parents=True)
    model,train_info=train_model()
    modelp=ROOT/'fluo_gb_signature_model.joblib';dump(model,modelp,compress=3)
    all_m=[];all_e=[]
    for phase,seeds in [('development',[20261101,20261102,20261103]),('locked',[20261201,20261202])]:
        for seed in seeds:
            folder=ROOT/'data'/phase/str(seed)
            if not (folder/'fluo_manifest.json').exists():continue
            sensor=pd.read_csv(folder/'fluo_sensor_stream.csv.gz')
            output=inference(sensor,model)
            assert len(output)==len(sensor)
            metrics,ep=evaluate(output,folder,phase,seed)
            all_m.append(metrics);all_e.append(ep)
            if phase=='locked':output.to_csv(ROOT/f'locked_predictions_{seed}.csv.gz',index=False,compression={'method':'gzip','compresslevel':6,'mtime':0})
            print('RUN',phase,seed,metrics[['method','physical_detected','physical_total','transport_delay_warned','transport_delay_total','clean_clusters_per_100h']].to_string(index=False),flush=True)
    metrics=pd.concat(all_m,ignore_index=True);events=pd.concat(all_e,ignore_index=True)
    metrics.to_csv(ROOT/'cohort_metrics.csv',index=False);events.to_csv(ROOT/'cohort_episode_evaluation.csv',index=False)
    summary=metrics.groupby(['phase','method']).agg(physical_detected=('physical_detected','sum'),physical_total=('physical_total','sum'),sensor_bias_warned=('sensor_bias_warned','sum'),sensor_bias_total=('sensor_bias_total','sum'),transport_delay_warned=('transport_delay_warned','sum'),transport_delay_total=('transport_delay_total','sum'),dropout_warned=('dropout_warned','sum'),dropout_total=('dropout_total','sum'),offline_warned=('offline_warned','sum'),offline_total=('offline_total','sum'),clean_false_clusters=('clean_false_clusters','sum'),clean_hours=('clean_hours','sum'),scoreable_minutes=('scoreable_minutes','sum'),total_minutes=('total_minutes','sum')).reset_index()
    summary['physical_event_recall']=summary.physical_detected/summary.physical_total
    summary['clean_false_clusters_per_100h']=100*summary.clean_false_clusters/summary.clean_hours
    delays=events[(events.event_group=='physical_loss') & events.detected].groupby(['phase','method'])['first_warning_delay_min'].median()
    summary['median_first_warning_delay_min']=[float(delays.get((x.phase,x.method),np.nan)) for x in summary.itertuples()]
    summary.to_csv(ROOT/'aggregate_metrics.csv',index=False)
    config={'model':'HistGradientBoostingClassifier','model_init':{'max_iter':75,'max_leaf_nodes':9,'min_samples_leaf':70,'l2_regularization':3.,'learning_rate':.05,'random_state':SEED},'train':train_info,'methods_and_frozen_thresholds':THRESHOLDS,'threshold_selected_with_development_seeds':[20261101,20261102,20261103],'locked_evaluation_seeds':[20261201,20261202],'persistence':{'window_min':WINDOW,'min_exceedances':K,'minimum_production_warmup_min':WARMUP,'reconnect_valid_history_min':RECONNECT},'constraints':['Input from sensor only; synthetic oracle used exclusively as supervised TARGET in original TRAIN and evaluation after scoring.','ML score is NOT calibrated probability of physical loss.','Return meter bias and physical return deficit may be observationally indistinguishable.','Other synthetic seeds are same generator family; no industrial/external validity.','No valve actuation or authorization of recovered condensate.'],'software':{'python':platform.python_version(),'numpy':version('numpy'),'pandas':version('pandas'),'scikit-learn':version('scikit-learn')}}
    (ROOT/'frozen_experiment_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False))
    (ROOT/'p2_io_contract.json').write_text(json.dumps({'input':'one site-sorted synthetic sensor stream, same 13 columns','required_numeric_units':'steam/return kg/h; pressure bar(g); temp C','features':FEATURES,'output':{'triage_status':['DATA_OR_MODE_CHECK','INVESTIGATE_RETURN_DEFICIT_UNCONFIRMED','MONITOR'],'next_safe_action':'inspection-only human decision','recovery_eligibility':'UNKNOWN_REQUIRES_SITE_ASSESSMENT','auto_actuation_allowed':False,'gb_signature_score':'uncalibrated synthetic score, never true-loss probability'},'alert_logic':'5 of last 10 production/valid minutes above GB .90','safety':'no automatic valve/boiler command; verify meter and condensate quality before any recovery advice'},indent=2))
    print('\nAGGREGATE\n',summary.to_string(index=False),flush=True)
if __name__=='__main__':main()
