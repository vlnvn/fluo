#!/usr/bin/env python3
"""Frozen synthetic holdout evaluation; never tunes parameters on fresh holdout."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from scipy.stats import beta
from joblib import load
from compare_models import ROOT,HERE,fmt_data,FEATURES,alert,summarize

SEEDS=[20270111,20270112]

def ci(k,n):
 if not n:return [None,None]
 return [0 if k==0 else float(beta.ppf(.025,k,n-k+1)),1 if k==n else float(beta.ppf(.975,k+1,n-k))]

def main():
 frozen=json.loads((HERE/'reports'/'frozen_selection.json').read_text())
 assert frozen['selected']=={'model':'hgb_v2','threshold':.9,'selection_status':'meet development gate'}
 model=load(HERE/'selected_model.joblib')
 allrows=[];stress=[]
 for seed in SEEDS:
  f=ROOT/'fresh_holdout'/str(seed)
  raw=pd.read_csv(f/'fluo_sensor_stream.csv.gz'); eps=pd.read_csv(f/'fluo_episode_labels.csv')
  for condition in ('original','return_meter_minus_5pct','return_meter_minus_10pct','steam_meter_plus_5pct'):
   x=raw.copy()
   if condition=='return_meter_minus_5pct': x['condensate_return_obs_kg_h']*=.95
   if condition=='return_meter_minus_10pct':x['condensate_return_obs_kg_h']*=.90
   if condition=='steam_meter_plus_5pct':x['steam_flow_obs_kg_h']*=1.05
   d=fmt_data(x);d.attrs['directory']=f
   valid=d.decision_valid.to_numpy();score=np.full(len(d),np.nan)
   score[valid]=model.predict_proba(d.loc[valid,FEATURES].to_numpy(float))[:,1]
   z=summarize(d,score,.90,eps)
   allrows.append(dict(seed=seed,condition=condition,**z))
   print('RESULT',seed,condition, 'physical',z['phys_det'],'/',z['phys_total'],'delay disturbance',z['shift_det'],'/',z['shift_total'],'normal alerts',z['unmarked_warning_minutes'],'/',z['unmarked_valid_minutes'],flush=True)
 summary=pd.DataFrame(allrows)
 summary.to_csv(HERE/'reports'/'fresh_holdout_robustness.csv',index=False)
 clean=summary[summary.condition.eq('original')]
 k=int(clean.phys_det.sum());n=int(clean.phys_total.sum())
 shift=int(clean.shift_det.sum());shift_n=int(clean.shift_total.sum());bias=int(clean.bias_det.sum());bias_n=int(clean.bias_total.sum())
 overview={'frozen_method':'hgb_v2','threshold':.9,'fresh_holdout_seeds':SEEDS,'synthetic_telemetry_rows':172800,
           'physical_events_detected':k,'physical_events_total':n,'physical_recall':k/n,
           'descriptive_clopper_pearson_95_interval':ci(k,n),'interval_not_industrial_performance_estimate':True,
           'transport_shift_alerted':shift,'transport_shift_total':shift_n,
           'meter_bias_alerted':bias,'meter_bias_total':bias_n,
           'clean_clusters':int(clean.clean_clusters.sum()),'clean_hours':float(clean.clean_hours.sum()),
           'unmarked_warning_minutes':int(clean.unmarked_warning_minutes.sum()),'unmarked_valid_minutes':int(clean.unmarked_valid_minutes.sum()),
           'limits':['all configurations from same simulator family','physical loss and meter bias not identifiable from paired steam/return flow alone','5%/10% meter drift robustness evaluated post selection, never used to select model','field performance unknown']}
 (HERE/'reports'/'fresh_holdout_summary.json').write_text(json.dumps(overview,indent=2))
 print('SUMMARY',json.dumps(overview,indent=2),flush=True)

if __name__=='__main__':main()
