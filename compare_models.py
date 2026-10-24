#!/usr/bin/env python3
"""Development-only candidate comparison for synthetic deficit monitoring.
Never uses prior locked cohorts to select an algorithm.
"""
from pathlib import Path
import sys,json
import numpy as np,pandas as pd
from joblib import load,dump
from sklearn.ensemble import ExtraTreesClassifier,HistGradientBoostingClassifier
from lightgbm import LGBMClassifier
HERE=Path(__file__).resolve().parent
SRC=HERE
sys.path.insert(0,str(SRC))
from run_fluo_v2 import fmt_data, FEATURES

ROOT=HERE/'data'
CONFIG={'models':['hgb_v2','extra_trees','lightgbm'],'thresholds':[.70,.80,.90,.95], 'persistence':{'window':10,'hits':5},'selection':'no model selected from prior locked results; use development scenarios only'}

def train():
    s=pd.read_csv(ROOT/'original'/'fluo_sensor_stream.csv.gz')
    truth=pd.read_csv(ROOT/'original'/'fluo_physics_ground_truth.csv.gz',usecols=['site_id','minute_id','event_type'])
    d=fmt_data(s)
    truth=d[['site_id','minute_id']].merge(truth,on=['site_id','minute_id'],validate='one_to_one')
    y=truth.event_type.isin(['diversion_to_pit','return_pipe_loss','trap_blowthrough','return_meter_bias']).to_numpy()
    mask=d.split.eq('train')&d.decision_valid
    X=d.loc[mask,FEATURES].to_numpy(float); y=y[mask.to_numpy()].astype(int)
    assert X.shape[0]==len(y)
    models={
    'hgb_v2':HistGradientBoostingClassifier(max_iter=75,max_leaf_nodes=9,min_samples_leaf=70,l2_regularization=3.,learning_rate=.05,random_state=71),
    'extra_trees':ExtraTreesClassifier(n_estimators=160,min_samples_leaf=16,max_features=.8,n_jobs=3,random_state=71),
    'lightgbm':LGBMClassifier(n_estimators=90,max_depth=5,num_leaves=13,min_child_samples=80,learning_rate=.05,reg_lambda=3.,verbose=-1,n_jobs=3,random_state=71)
    }
    for name,m in models.items():m.fit(X,y)
    return models

def alert(scores,valid,sites,threshold,window=10,hits=5):
    candidate=(scores>threshold)&valid&np.isfinite(scores)
    return pd.Series(candidate).groupby(sites).transform(lambda x:x.rolling(window,min_periods=window).sum().ge(hits)).to_numpy()&valid

def summarize(d,score,threshold,eps):
    gate=d.decision_valid.to_numpy(); alarm=alert(score,gate,d.site_id.to_numpy(),threshold)
    # Count independent episode detections only inside onset->end
    df=d[['site_id','timestamp','minute_id']].copy();df['timestamp']=pd.to_datetime(df['timestamp'],utc=True);df['alarm']=alarm
    rows=[]
    for e in eps.itertuples(index=False):
        t1=pd.Timestamp(e.start_timestamp);t2=pd.Timestamp(e.end_timestamp_inclusive)
        g=df[(df.site_id==e.site_id)&df.timestamp.between(t1,t2)]
        seen=g[g.alarm]
        rows.append((e.event_group,e.event_type,bool(len(seen)),int((seen.iloc[0].timestamp-t1).total_seconds()/60) if len(seen) else None))
    er=pd.DataFrame(rows,columns=['group','type','detected','delay'])
    phys=er[er.group=='physical_loss']; shift=er[er.type=='transport_delay_shift']; bias=er[er.type=='return_meter_bias']
    # 'clean' means more than 45 min outside every injected event, an optimistic subset.
    truth=pd.read_csv((d.attrs['directory'])/'fluo_physics_ground_truth.csv.gz',usecols=['site_id','minute_id','event_type'])
    truth=d[['site_id','minute_id']].merge(truth,on=['site_id','minute_id'],validate='one_to_one')
    eventnear=np.zeros(len(d),bool)
    for site,g in d.groupby('site_id',sort=False):
        ix=g.index.to_numpy(); eventnear[ix]=pd.Series(truth.loc[ix,'event_type'].ne('none').to_numpy()).rolling(91,center=True,min_periods=1).max().fillna(0).gt(0).to_numpy()
    clean=(~eventnear)&gate
    # clusters grouped by within-site continuous valid minutes
    count=0
    for site,g in d[clean].groupby('site_id'):
        minutes=g.loc[alarm[g.index], 'minute_id'].to_numpy()
        if len(minutes):count+=int(1+(np.diff(minutes)>30).sum())
    # normal hours incl aftereffects, separately reported (less optimistic)
    unmarked=truth.event_type.eq('none').to_numpy()&gate
    nwarning=int((alarm&unmarked).sum())
    return dict(phys_det=int(phys.detected.sum()),phys_total=len(phys),shift_det=int(shift.detected.sum()),shift_total=len(shift),bias_det=int(bias.detected.sum()),bias_total=len(bias),clean_clusters=count,clean_hours=round(clean.sum()/60,3),unmarked_warning_minutes=nwarning,unmarked_valid_minutes=int(unmarked.sum()),median_delay=float(phys.loc[phys.detected,'delay'].median()) if phys.detected.sum() else np.nan)

def eval_cohort(models,phase,seeds,thresholds):
    records=[]
    for seed in seeds:
        folder=ROOT/phase/str(seed)
        s=pd.read_csv(folder/'fluo_sensor_stream.csv.gz')
        d=fmt_data(s);d.attrs['directory']=folder
        eps=pd.read_csv(folder/'fluo_episode_labels.csv')
        gate=d.decision_valid.to_numpy()
        X=d.loc[gate,FEATURES].to_numpy(float)
        for name,model in models.items():
            score=np.full(len(d),np.nan)
            score[gate]=model.predict_proba(X)[:,1]
            for thr in thresholds:
                z=summarize(d,score,thr,eps)
                records.append(dict(phase=phase,seed=seed,model=name,threshold=thr,**z))
        print('cohort finished',phase,seed,flush=True)
    return pd.DataFrame(records)

def pick(df):
    groups=df.groupby(['model','threshold'],as_index=False).agg(phys_det=('phys_det','sum'),phys_total=('phys_total','sum'),shift_det=('shift_det','sum'),shift_total=('shift_total','sum'),bias_det=('bias_det','sum'),bias_total=('bias_total','sum'),clean_clusters=('clean_clusters','sum'),clean_hours=('clean_hours','sum'),unmarked_warning_minutes=('unmarked_warning_minutes','sum'),unmarked_valid_minutes=('unmarked_valid_minutes','sum'),median_delay=('median_delay','median'))
    groups['physical_recall']=groups.phys_det/groups.phys_total
    groups['clean_alarm_per100h']=groups.clean_clusters/(groups.clean_hours/100)
    groups['unmarked_warn_fraction']=groups.unmarked_warning_minutes/groups.unmarked_valid_minutes
    # Fixed decision rule specified for dev; choose minimal nuisance with recall >= 98%, then speed.
    ok=groups[(groups.physical_recall>=.98)&(groups.clean_alarm_per100h<=.5)]
    if len(ok):
        ok=ok.sort_values(['shift_det','unmarked_warn_fraction','median_delay','model'])
        best=ok.iloc[0]
        status='meet development gate'
    else:
        best=groups.sort_values(['physical_recall','shift_det','clean_alarm_per100h'],ascending=[False,True,True]).iloc[0]
        status='no model meets development gate'
    return groups,dict(model=str(best.model),threshold=float(best.threshold),selection_status=status)

if __name__=='__main__':
    out=HERE/'reports';out.mkdir(exist_ok=True)
    models=train(); print('train complete',list(models),flush=True)
    dev=eval_cohort(models,'development',[20261101,20261102,20261103],CONFIG['thresholds'])
    dev.to_csv(out/'development_candidates.csv',index=False)
    agg,best=pick(dev);agg.to_csv(out/'development_summary.csv',index=False)
    (out/'frozen_selection.json').write_text(json.dumps({**CONFIG,'selected':best},indent=2))
    dump(models[best['model']],HERE/'selected_model.joblib',compress=3)
    print('DEVELOPMENT WINNER',best,flush=True)
    print(agg.sort_values(['shift_det','physical_recall'],ascending=[True,False]).to_string(index=False),flush=True)
