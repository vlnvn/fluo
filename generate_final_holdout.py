#!/usr/bin/env python3
"""Generate new synthetic evaluation cohorts after freezing selection.
These are NOT independent physical plant datasets; same simulator family.
"""
import json
from pathlib import Path
import generate_fluo as gen
HERE=Path(__file__).resolve().parent
SEEDS=(20270111,20270112)

def main():
 selection=json.loads((HERE/'reports'/'frozen_selection.json').read_text())
 assert selection['selected']['model']=='hgb_v2' and selection['selected']['threshold']==0.9
 original=gen.CONFIGS
 for seed in SEEDS:
  out=HERE/'data'/'fresh_holdout'/str(seed)
  if (out/'fluo_manifest.json').exists(): continue
  gen.SEED=seed
  first=tuple(dict(c,split_segments=(('test_configuration',12),)) for c in original)
  d=dict(original[0]);d.update(site_id='CFG_D',rated_steam_kg_h=350.,steam_pressure_setpoint_barg=4.,receiver_tau_min=16.,split_segments=(('test_configuration',12),))
  e=dict(original[1]);e.update(site_id='CFG_E',rated_steam_kg_h=170.,steam_pressure_setpoint_barg=6.,receiver_tau_min=2.,split_segments=(('test_configuration',12),))
  gen.CONFIGS=first+(d,e)
  gen.generate(out)
  print('GENERATED',seed,flush=True)
 gen.CONFIGS=original

if __name__=='__main__': main()
