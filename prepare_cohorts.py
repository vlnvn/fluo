#!/usr/bin/env python3
"""Generate explicitly artificial development/locked evaluation scenarios.
The generators use SAME SIMULATOR PHYSICS as v1, so NOT independent physical validation.
"""
from pathlib import Path
import sys, json, importlib.util
sys.path.insert(0,str(Path(__file__).resolve().parent))
import generate_fluo as g
ROOT=Path(__file__).resolve().parent
# distinct seeds; not drawn from secrets; their purpose is a fresh split, not security
DEV_SEEDS=[20261101,20261102,20261103]
LOCKED_SEEDS=[20261201,20261202]

def run():
    default_cfg=g.CONFIGS
    for phase,seeds in [('development',DEV_SEEDS),('locked',LOCKED_SEEDS)]:
        for seed in seeds:
            out=ROOT/'data'/phase/str(seed)
            if (out/'fluo_sensor_stream.csv.gz').exists():continue
            print('GENERATE',phase,seed,flush=True)
            g.SEED=seed
            if phase=='locked':
                # A/B/C changes + 2 additional out-of-config scenarios.  Numeric values are unmeasured synthetic stress settings.
                new_cfgs=tuple(dict(c, split_segments=(('test_configuration',12),)) for c in default_cfg)
                x=dict(default_cfg[0]);x.update(site_id='CFG_D',rated_steam_kg_h=350.,steam_pressure_setpoint_barg=4.,receiver_tau_min=16.,split_segments=(('test_configuration',12),))
                y=dict(default_cfg[1]);y.update(site_id='CFG_E',rated_steam_kg_h=170.,steam_pressure_setpoint_barg=6.,receiver_tau_min=2.,split_segments=(('test_configuration',12),))
                g.CONFIGS=tuple(new_cfgs)+(x,y)
            else:g.CONFIGS=default_cfg
            g.generate(out)
    g.CONFIGS=default_cfg
    (ROOT/'cohort_registry.json').write_text(json.dumps({'development_seeds':DEV_SEEDS,'locked_seeds':LOCKED_SEEDS,'notes':'All entirely synthetic, same governing generator; CFG_D/E are arbitrary additional stress configs. Do not label independent real-world domain.'},indent=2))
if __name__=='__main__':run()
