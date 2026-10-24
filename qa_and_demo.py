"""Integration and evidence/triage safeguards for synthetic prototype."""
from pathlib import Path
import json,sys
import pandas as pd,numpy as np
from joblib import load
from run_fluo_v2 import ROOT,inference,FEATURES

def main():
 model=load(ROOT/'fluo_gb_signature_model.joblib')
 path=ROOT/'data'/'locked'/'20261201'
 sensor=pd.read_csv(path/'fluo_sensor_stream.csv.gz')
 labels=pd.read_csv(path/'fluo_physics_ground_truth.csv.gz',usecols=['site_id','minute_id','event_type'])
 pred=inference(sensor,model)
 assert len(pred)==len(sensor)
 # Production/field interface and malformed inputs are refused rather than silently scoring.
 for bad, mode in [(sensor.head(3), 'FIELD_DEPLOYMENT'), (sensor.head(3).drop(columns=['steam_flow_obs_kg_h']),'SYNTHETIC_REPLAY')]:
  try:
   inference(bad,model,run_mode=mode)
   raise AssertionError('Expected explicit fail-closed exception')
  except (RuntimeError,ValueError): pass
 bad=sensor.head(3).copy();bad.loc[bad.index[0],'steam_flow_obs_kg_h']=-5.
 try:
  inference(bad,model)
  raise AssertionError('Negative flow must be rejected')
 except ValueError: pass
 assert pred.auto_actuation_allowed.eq(False).all()
 assert pred.recovery_eligibility.eq('UNKNOWN_REQUIRES_SITE_ASSESSMENT').all()
 assert pred.score_meaning.str.contains('not physical-loss probability').all()
 assert not pred.loc[pred.quality_action.ne('SCORE_ALLOWED'),'gb_signature_warning'].any()
 assert not pred.loc[pred.link_online.eq(0),'gb_signature_warning'].any()
 assert not pred.loc[pred.condensate_return_obs_kg_h.isna(),'gb_signature_warning'].any()
 assert not pred.loc[pred.operating_mode.ne('production'),'gb_signature_warning'].any()
 assert not pred.columns.str.contains('event_group|event_type|event_id|true_loss|ground_truth').any()
 assert 'return_meter_bias' in labels.event_type.values
 # Selected cases for demonstration with oracle in test-script only, not part of online input or output.
 joined=pred.merge(labels,on=['site_id','minute_id'],validate='one_to_one')
 examples=[]
 cases=[('confirmed_injected_physical_loss','diversion_to_pit',True),
        ('injected_meter_bias_ambiguous','return_meter_bias',True),
        ('injected_transport_delay_no_alert','transport_delay_shift',False),
        ('offline_requires_quality_gate','network_outage',False),
        ('meter_dropout_requires_quality_gate','return_meter_dropout',False),
        ('normal_monitor','none',False)]
 for label,kind,warn in cases:
  subset=joined[joined.event_type.eq(kind)&joined.gb_signature_warning.eq(warn)]
  if kind=='none':subset=subset[subset.quality_action.eq('SCORE_ALLOWED')]
  if len(subset)==0:subset=joined[joined.event_type.eq(kind)]
  if len(subset)==0:continue
  x=subset.iloc[len(subset)//2]
  record={'test_selection':label,'oracle_event_type_USED_ONLY_FOR_QA':kind,
   'simulated_operator_view':{
       'time':x.timestamp,'site_id':x.site_id,'steam_flow_kg_h':float(x.steam_flow_obs_kg_h),
       'condensate_return_flow_kg_h':None if pd.isna(x.condensate_return_obs_kg_h) else float(x.condensate_return_obs_kg_h),
       'quality_action':x.quality_action,'ml_signature_score':None if pd.isna(x.gb_signature_score) else round(float(x.gb_signature_score),5),
       'warning':bool(x.gb_signature_warning),'triage_status':x.triage_status,
       'next_safe_action':x.next_safe_action,'condensate_recovery':'UNKNOWN — quality test and engineer approval required',
       'automatic_valve_action':False,'data_tag':'FULLY_SYNTHETIC_REPLAY; not site-commissioned'}}
  examples.append(record)
 (ROOT/'P2_synthetic_action_card_examples.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2))
 qa={'qa_status':'PASS_FOR_SYNTHETIC_REPLAY_ONLY',
     'checks':{'sensor_input_only':True,'oracle_not_in_runtime_columns':True,'no_offline_alarm':True,
               'no_missing_flow_alarm':True,'no_nonproduction_alarm':True,'no_automatic_actuation':True,
               'recovery_quality_always_unknown':True,'score_not_causal_probability':True,'real_field_mode_denied':True,'missing_fields_denied':True,'negative_flow_denied':True},
     'readiness_gate':{'synthetic_lab_demo':'GO','industrial_recovery_decision':'NO_GO',
          'industrial_real_time_alarm':'NO_GO until field calibration, safety review and validation'},
     'example_scenarios':len(examples)}
 (ROOT/'P2_integration_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
 print(json.dumps(qa,indent=2))
 for e in examples:print(e['test_selection'],e['simulated_operator_view']['triage_status'],e['simulated_operator_view']['warning'])
if __name__=='__main__':main()
