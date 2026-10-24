#!/usr/bin/env python3
"""FLUO v1 real synthetic-only benchmark. 2026-10-24.
No ground-truth data used for fit, feature creation or score calibration.
Evaluation labels joined only after models & thresholds are frozen.
"""
from __future__ import annotations
import json, math, hashlib, argparse, zipfile, sys, gzip
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from joblib import dump

SEED=20261024
Q=0.99   # predetermined validation-score percentile, no evaluation labels
WINDOW=5
K=3
COOLDOWN=30
F=['loss_ratio_instant','loss_ratio_ewma5','loss_ratio_ewma15','ratio_return_steam','return_to_expected_ewma5','steam_step_rel','steam_rolling_cv','return_rolling_cv','temperature_delta_saturation','return_temperature_obs_C']
REFERENCE={"R1":"https://www.forbesmarshall.com/country-highlights-indonesia/optimising-energy-and-efficiency-at-a-textile-plant-in-western-indonesia/","R2":"https://www.spiraxsarco.com/learn-about-steam/steam-engineering-principles-and-heat-transfer/what-is-steam","R3":"https://www.spiraxsarco.com/learn-about-steam/condensate-recovery/flash-steam","R4":"https://www.osti.gov/biblio/15000711","R6":"https://downloads.unido.org/ot/47/89/4789812/10001-15000_10251.pdf"}


def read_data(src):
    src=Path(src)
    if src.is_file() and src.suffix=='.zip':
        with zipfile.ZipFile(src) as z:
            def get(n):
                member=next(x for x in z.namelist() if x.endswith('/'+n))
                with z.open(member) as io:
                    if n.endswith(".gz"):
                        with gzip.GzipFile(fileobj=io) as gz:return pd.read_csv(gz)
                    return pd.read_csv(io)
            s=get('fluo_sensor_stream.csv.gz'); episodes=get('fluo_episode_labels.csv')
        return s,episodes
    return pd.read_csv(src/'fluo_sensor_stream.csv.gz'),pd.read_csv(src/'fluo_episode_labels.csv')


def build_features(raw):
    data=raw.copy().sort_values(['site_id','minute_id'],kind='stable').reset_index(drop=True)
    data['timestamp_dt']=pd.to_datetime(data['timestamp'],utc=True)
    # physically motivated flash fraction, no true simulator state or generator-specific config.
    # fixed 2 deg C synthetic subcooling proxy: not known as a facility parameter.
    pressures=np.array([0,1,2,3,4,5,6,7],dtype=float)
    hf=np.array([419,506,562,605,641,671,697,721],dtype=float)
    p=np.clip(data['steam_pressure_obs_barg'].to_numpy(float),0,7)
    flash=np.maximum((np.interp(p,pressures,hf)-419.-4.18*2.)/2257.,0.)
    steam=data['steam_flow_obs_kg_h'].to_numpy(float)
    steam_liquid=np.clip(steam*(1.-flash),0,None)
    # fixed tau=8 min pooled engineering assumption; NEVER use unseen site ground-truth tau.
    # only past/current observations, no centered rolling or future shift.
    out=[]
    for site,g in data.groupby('site_id',sort=False):
        ind=g.index.to_numpy()
        expected=pd.Series(steam_liquid[ind]).ewm(alpha=1./9.,adjust=False).mean().to_numpy()
        ret=g['condensate_return_obs_kg_h'].astype(float)
        # missing return remains missing: no interpolation through fault or offline intervals
        denom=np.maximum(expected,8.)
        instant=(expected-ret.to_numpy())/denom
        ratio=(ret.to_numpy())/np.maximum(steam[ind],8.)
        feat=pd.DataFrame(index=ind)
        feat['loss_ratio_instant']=instant
        feat['loss_ratio_ewma5']=pd.Series(instant).ewm(span=5,adjust=False,ignore_na=True).mean().to_numpy()
        feat['loss_ratio_ewma15']=pd.Series(instant).ewm(span=15,adjust=False,ignore_na=True).mean().to_numpy()
        feat['ratio_return_steam']=ratio
        feat['return_to_expected_ewma5']=pd.Series(ret.to_numpy()/denom).ewm(span=5,adjust=False,ignore_na=True).mean().to_numpy()
        steam_s=pd.Series(steam[ind])
        feat['steam_step_rel']=np.nan_to_num(steam_s.diff().to_numpy()/np.maximum(steam_s.shift(1).to_numpy(),8.),nan=0.)
        feat['steam_rolling_cv']=(steam_s.rolling(15,min_periods=3).std()/(steam_s.rolling(15,min_periods=3).mean()+8.)).fillna(0).to_numpy()
        ret_s=ret.rolling(15,min_periods=3)
        feat['return_rolling_cv']=(ret_s.std()/(ret_s.mean()+8.)).to_numpy()
        feat['temperature_delta_saturation']=g['steam_temperature_obs_C'].to_numpy(float)-np.interp(p[ind],pressures,[100,120,134,144,152,159,165,170])
        feat['return_temperature_obs_C']=g['return_temperature_obs_C'].to_numpy(float)
        out.append(feat)
    feature=pd.concat(out).sort_index()
    for col in F: data[col]=feature[col].to_numpy()
    # Causal quality gating. Gate prevents imputing outages/missing meter as physical-loss alerts.
    data['gate_valid']= (data['link_online'].eq(1)&data['data_quality_flag'].eq('observed')& data['operating_mode'].eq('production')&data[F].notna().all(axis=1)&np.isfinite(data[F]).all(axis=1))
    data['quality_action']=np.select([data['link_online'].eq(0),data['condensate_return_obs_kg_h'].isna(),~data['operating_mode'].eq('production')],['GATEWAY_OFFLINE','CHECK_RETURN_METER','OUT_OF_SCOPE_MODE'],default='SCORE')
    return data


def calibrate(scores,valmask):
    x=scores[valmask & np.isfinite(scores)]
    return float(np.quantile(x,Q))


def event_metrics(data,episodes,predcol,split):
    sub=data[data['split'].eq(split)].copy()
    events=episodes[episodes['split'].eq(split)].copy()
    ep_rows=[]
    for ep in events.itertuples(index=False):
        t0=pd.Timestamp(ep.start_timestamp).tz_convert('UTC')
        t1=pd.Timestamp(ep.end_timestamp_inclusive).tz_convert('UTC')
        g=sub[(sub['site_id'].eq(ep.site_id))&(sub['timestamp_dt'].between(t0,t1))]
        inds=np.where(g[predcol].to_numpy(bool))[0]
        detected=len(inds)>0
        lead=int((g.iloc[inds[0]]['timestamp_dt']-t0).total_seconds()//60) if detected else None
        ep_rows.append(dict(split=split,site_id=ep.site_id,event_id=ep.event_id,event_type=ep.event_type,event_group=ep.event_group,duration_min=int(ep.duration_min),detected=bool(detected),first_alert_delay_min=lead,model=predcol))
    epf=pd.DataFrame(ep_rows)
    phys=epf[epf.event_group.eq('physical_loss')]
    sens=epf[epf.event_group.eq('sensor_fault')]
    dist=epf[epf.event_group.eq('nonloss_disturbance')]
    # nuisance per non-physical *valid* hour: physical truth labels are used here ONLY in evaluation.
    nuisance=sub.loc[~sub['true_physical_loss'] & sub['gate_valid']]
    # count alert clusters with >=30min gap per site
    alert_starts=0
    for _,g in nuisance.groupby('site_id'):
        which=np.flatnonzero(g[predcol].to_numpy(bool))
        if len(which):
            mins=g.iloc[which]['minute_id'].to_numpy()
            alert_starts+=int(1+np.sum(np.diff(mins)>COOLDOWN))
    valid_h=len(nuisance)/60.
    warning_mins=int(sub[predcol].sum())
    phys_mins=sub[sub.true_physical_loss]
    return {
      'model':predcol,'split':split,'n_rows':len(sub),'n_valid_minutes':int(sub.gate_valid.sum()),
      'physical_episodes':len(phys),'physical_episodes_detected':int(phys.detected.sum()),
      'event_recall':float(phys.detected.mean()) if len(phys) else None,
      'physical_minutes':len(phys_mins),'physical_minutes_flagged':int(phys_mins[predcol].sum()),
      'physical_minute_recall':float(phys_mins[predcol].mean()) if len(phys_mins) else None,
      'nonphysical_valid_hours':round(valid_h,3),'nuisance_alert_clusters':alert_starts,
      'nuisance_clusters_per_100h':float(alert_starts/(valid_h/100)) if valid_h else None,
      'warning_minutes':warning_mins,'sensor_fault_episodes':len(sens),'sensor_fault_episodes_flagged':int(sens.detected.sum()),
      'nonloss_episodes':len(dist),'nonloss_episodes_flagged':int(dist.detected.sum()),
      'median_first_detection_delay_min':float(phys[phys.detected].first_alert_delay_min.median()) if phys.detected.sum() else None,
      'quality_coverage_rate':float(sub.gate_valid.mean()),
    },epf


def apply_alert(scores,thresholds,data,scorename):
    # threshold fixed on validation without labels; quality gating then 3-out-of-5 persistence.
    candidate=np.isfinite(scores)&(scores>thresholds)&data.gate_valid.to_numpy()
    ser=pd.Series(candidate,index=data.index)
    persistent=np.zeros(len(data),dtype=bool)
    for _,g in data.groupby('site_id',sort=False):
        inds=g.index
        persistent[inds]=ser.loc[inds].rolling(WINDOW,min_periods=WINDOW).sum().ge(K).to_numpy()
    return candidate,persistent & data.gate_valid.to_numpy()


def run(src,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    raw,episodes=read_data(src)
    data=build_features(raw)
    for split in ['train','validation','test_temporal','test_configuration']:
        assert (data.split.eq(split)).sum()=={'train':17280,'validation':8640,'test_temporal':8640,'test_configuration':17280}[split]
    train=data.split.eq('train')&data.gate_valid
    val=data.split.eq('validation')&data.gate_valid
    scaler=RobustScaler(quantile_range=(10,90)).fit(data.loc[train,F])
    estimator=IsolationForest(n_estimators=250,max_samples=1024,max_features=0.9,contamination='auto',random_state=SEED,n_jobs=2)
    estimator.fit(scaler.transform(data.loc[train,F]))
    valid=data.gate_valid
    scores={}
    # simple threshold: smaller return / current steam => larger score. No normality labels used.
    scores['fixed_ratio']=pd.Series(1.-data['condensate_return_obs_kg_h']/np.maximum(data['steam_flow_obs_kg_h'],8.),index=data.index).to_numpy()
    # physically motivated residual from causal estimate, same global lag assumption for unseen configuration.
    scores['physical_residual']=data['loss_ratio_ewma5'].to_numpy(dtype=float)
    sc_if=np.full(len(data),np.nan)
    sc_if[valid.to_numpy()]=-estimator.decision_function(scaler.transform(data.loc[valid,F]))
    scores['isolation_forest']=sc_if
    thresholds={k:calibrate(v,val.to_numpy()) for k,v in scores.items()}
    for name,scores_arr in scores.items():
        _,pred=apply_alert(scores_arr,thresholds[name],data,name)
        data['alert_'+name]=pred
        data['score_'+name]=scores_arr
    # EVALUATION GROUND TRUTH JOIN OCCURS AFTER ALL TRAINING / THRESHOLD CALIBRATION
    masktruth=np.zeros(len(data),dtype=bool)
    for ep in episodes.itertuples(index=False):
        if ep.event_group!='physical_loss': continue
        t0=pd.Timestamp(ep.start_timestamp).tz_convert('UTC');t1=pd.Timestamp(ep.end_timestamp_inclusive).tz_convert('UTC')
        masktruth |= (data.site_id.eq(ep.site_id)&data.timestamp_dt.between(t0,t1)).to_numpy()
    data['true_physical_loss']=masktruth
    rows=[];all_eps=[]
    for split in ['validation','test_temporal','test_configuration']:
        for name in scores:
            rr,ee=event_metrics(data,episodes,'alert_'+name,split)
            rr['model']=name
            ee['model']=name
            rows.append(rr);all_eps.append(ee)
    report=pd.DataFrame(rows)
    per_ep=pd.concat(all_eps,ignore_index=True)
    # frozen model artifact. Use with exact versioned preprocessing function, not blindly predict raw CSV.
    dump({'estimator':estimator,'scaler':scaler,'feature_names':F,'thresholds':thresholds,'score_quantile':Q,'seed':SEED,'persistence':{'window':WINDOW,'hits':K},'config_policy':'no site-specific fit for held-out CFG_C','not_field_validated':True},out/'fluo_iforest_model.joblib',compress=3)
    cols=['timestamp','site_id','minute_id','split','operating_mode','gate_valid','quality_action']+[c for c in data if c.startswith('score_') or c.startswith('alert_')]
    data[cols].to_csv(out/'fluo_predictions.csv.gz',index=False,compression={'method':'gzip','compresslevel':6,'mtime':0})
    report.to_csv(out/'fluo_metrics.csv',index=False)
    per_ep.to_csv(out/'fluo_episode_evaluation.csv',index=False)
    cfg={'seed':SEED,'python':sys.version,'pandas':pd.__version__,'sklearn':__import__('sklearn').__version__,'model':'IsolationForest','train_strategy':'all valid production data including unlabeled injected events, with NO oracle filtering','feature_names':F,'score_threshold_rule':'99th percentile of validation scores on valid production rows (UNLABELED)','persistence':'3 of last 5 valid/current high scores, causal','fixed_tau_minutes':8,'calibration_uses_event_labels':False,'evaluation_labels_used_only_after_score_and_threshold_freeze':True,'split_policy':'train A/B, validation A/B, temporal test A/B, unseen-site C','thresholds':thresholds,'references':REFERENCE,'sensor_schema':list(raw.columns),'data_kind':'100% synthetic, no industrial accuracy claim','metrics_caveat':'36 injected episodes, only 2 physical events in each validation and temporal test; low precision; alert clusters measured in nonphysical valid periods; aftereffect outside oracle labels can inflate nuisance'}
    (out/'fluo_experiment_config.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding='utf8')
    # Output contract for P2: metadata + 1 decision per sample; gate before model; no claim leak location or recovery permission
    contract={'input':{'source':'fluo_sensor_stream.csv.gz','columns':list(raw.columns),'unit':'kg/h, bar(g), °C','quality_gating':'link_online=1, data_quality_flag=observed, production mode, feature completeness'},'output':{'timestamp':'ISO8601','site_id':'simulation site ID, not ML feature','quality_action':'GATEWAY_OFFLINE/CHECK_RETURN_METER/OUT_OF_SCOPE_MODE/SCORE','score_isolation_forest':'relative anomaly score, not probability','alert_isolation_forest':'boolean 3 of 5 threshold exceedances','triage_status':'pending P2 implementation; not automatically proved physical loss','recovery_authorization':'never; human engineer decides after physical assessment and condensate quality testing'},'safety':'no auto valve/boiler actuation; no actual recovery eligibility without plant data'}
    (out/'fluo_p2_io_contract.json').write_text(json.dumps(contract,indent=2,ensure_ascii=False),encoding='utf8')
    print(report[['split','model','physical_episodes_detected','physical_episodes','event_recall','nuisance_clusters_per_100h','sensor_fault_episodes_flagged','nonloss_episodes_flagged','physical_minute_recall']].to_string(index=False))
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='/mnt/data/FLUO_DEEPX_SYNTHETIC_DATASET_V1_20261024.zip');ap.add_argument('--out',default='/mnt/data/fluo_ml_v1');a=ap.parse_args();run(a.source,a.out)
