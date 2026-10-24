"""POST-HOC sensor shift stress tests. Diagnostic only; NOT blind test claims."""
from pathlib import Path
import pandas as pd,numpy as np,json
from joblib import load
from run_fluo_v2 import ROOT,inference
model=load(ROOT/'fluo_gb_signature_model.joblib')
rows=[]
for seed in [20261201,20261202]:
 folder=ROOT/'data'/'locked'/str(seed)
 raw=pd.read_csv(folder/'fluo_sensor_stream.csv.gz')
 truth=pd.read_csv(folder/'fluo_physics_ground_truth.csv.gz',usecols=['site_id','minute_id','event_group','event_type'])
 for condition in ['original','return_meter_95pct','return_meter_90pct','return_meter_105pct','steam_meter_105pct','return_multiplicative_noise_2pct']:
  x=raw.copy()
  if condition=='return_meter_95pct':x['condensate_return_obs_kg_h']*=.95
  if condition=='return_meter_90pct':x['condensate_return_obs_kg_h']*=.90
  if condition=='return_meter_105pct':x['condensate_return_obs_kg_h']*=1.05
  if condition=='steam_meter_105pct':x['steam_flow_obs_kg_h']*=1.05
  if condition=='return_multiplicative_noise_2pct':
   rng=np.random.default_rng(20261234+seed)
   x['condensate_return_obs_kg_h']*=rng.normal(1.,.02,len(x))
  p=inference(x,model)
  j=p.merge(truth,on=['site_id','minute_id'],validate='one_to_one')
  warn=j['gb_signature_warning']
  normal=j.event_type.eq('none') & j.quality_action.eq('SCORE_ALLOWED')
  # count contiguous alert bouts on observed normal rows, not just after-event guard
  clusters=0
  for site,g in j[normal].groupby('site_id'):
   mins=g.loc[g.gb_signature_warning,'minute_id'].to_numpy()
   if len(mins): clusters+=1+int((np.diff(mins)>30).sum())
  rows.append({'seed':seed,'stress':condition,'normal_warn_minutes':int((warn&normal).sum()),'normal_valid_minutes':int(normal.sum()),'normal_warn_clusters':clusters,'ambiguous_fault_warn_minutes':int((warn&j.event_type.eq('return_meter_bias')).sum()),'physical_warning_minutes':int((warn&j.event_group.eq('physical_loss')).sum())})
result=pd.DataFrame(rows);result.to_csv(ROOT/'POSTHOC_robustness_stress.csv',index=False)
print(result.to_string(index=False))
