#!/usr/bin/env python3
"""Fluo synthetic sizing steam-condensate dataset v1.0.

Reproducible engineering SCENARIOS, never operational observations from a textile plant.
Requires only numpy (plus the Python standard library). No internet needed.
Run: python generate_fluo.py --out ./data
"""
from __future__ import annotations
import argparse
import csv
import gzip
import io
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter
import numpy as np

VERSION = "fluo-synthetic-1.0"
SEED = 20261024
TZ = timezone(timedelta(hours=7))
START = datetime(2026, 1, 5, 0, 0, tzinfo=TZ)  # purely synthetic calendar index
STEP_MIN = 1
# Published saturated-steam table, Spirax Sarco: pressure bar(g), T_sat C, hf kJ/kg.
# Source: https://www.spiraxsarco.com/learn-about-steam/steam-engineering-principles-and-heat-transfer/what-is-steam
STEAM_TABLE = ((0.,100.,419.), (1.,120.,506.),(2.,134.,562.),(3.,144.,605.),
               (4.,152.,641.),(5.,159.,671.),(6.,165.,697.),(7.,170.,721.))
HF_ATM=419.0
HFG_ATM=2257.0
CP_WATER_APPROX=4.18  # kJ/kg/K design approximation, not textile measurement
CONFIGS = (
    # Reference 250 kg/h comes from an example in Spirax Sarco flash steam notes;
    # pressure combinations are experimental scenario design, NOT machinery specs.
    dict(site_id="CFG_A", rated_steam_kg_h=200.0, steam_pressure_setpoint_barg=3.0,
         receiver_tau_min=4.0, sizing_dryer_type="two_cylinder", kg_steam_per_kg_evaporated_liquid=2.3, split_segments=(("train",6),("validation",3),("test_temporal",3))),
    dict(site_id="CFG_B", rated_steam_kg_h=250.0, steam_pressure_setpoint_barg=5.0,
         receiver_tau_min=7.0, sizing_dryer_type="multi_cylinder", kg_steam_per_kg_evaporated_liquid=2.7, split_segments=(("train",6),("validation",3),("test_temporal",3))),
    dict(site_id="CFG_C", rated_steam_kg_h=300.0, steam_pressure_setpoint_barg=7.0,
         receiver_tau_min=11.0, sizing_dryer_type="multi_cylinder", kg_steam_per_kg_evaporated_liquid=5.6, split_segments=(("test_configuration",12),)),
)
# The above 200/250/300 and tau values are scenario assumptions, not observed textile data.
EVENTS_PER_DAY = 1.0  # TEST STRESS EXPOSURE, deliberately not an industry failure rate
EVENT_TYPES=("diversion_to_pit","return_pipe_loss","trap_blowthrough","return_meter_bias","return_meter_dropout","transport_delay_shift","network_outage")
EVENT_WEIGHTS=(0.20,0.16,0.14,0.16,0.11,0.13,0.10)  # deliberately enriched synthetic stress mix
SENSOR_FIELDS=("timestamp","site_id","minute_id","split","operating_mode","throughput_index",
               "steam_flow_obs_kg_h","condensate_return_obs_kg_h","steam_pressure_obs_barg",
               "steam_temperature_obs_C","return_temperature_obs_C","link_online","data_quality_flag")
TRUTH_FIELDS=("timestamp","site_id","minute_id","split","event_id","event_type","event_group",
              "steam_in_true_kg_h","condensate_return_true_kg_h","trap_blowthrough_true_kg_h",
              "flash_vent_true_kg_h","divert_to_pit_true_kg_h","return_line_loss_true_kg_h",
              "hold_up_kg","hold_up_change_kg_min","flash_mass_fraction","receiver_tau_active_min","liquid_evaporation_proxy_kg_h")
EPISODE_FIELDS=("site_id","split","event_id","event_type","event_group","start_timestamp",
                "end_timestamp_inclusive","duration_min","severity","severity_definition","parameter_provenance")

def sat_props(pressure_barg:float)->tuple[float,float]:
    grid=np.array(STEAM_TABLE)
    if pressure_barg<0. or pressure_barg>7.:
        raise ValueError("pressure must lie within published lookup [0,7] bar(g)")
    return float(np.interp(pressure_barg,grid[:,0],grid[:,1])),float(np.interp(pressure_barg,grid[:,0],grid[:,2]))

def generator_rows():
    counts=Counter(); cfgstats={}; episode_list=[]
    for site_idx,cfg in enumerate(CONFIGS):
        site=cfg["site_id"]
        rg=np.random.default_rng(SEED + site_idx*1009)
        total_days=sum(n for _,n in cfg["split_segments"])
        nrows=total_days*1440
        splits=[]
        for name,days in cfg["split_segments"]:
            splits.extend([name]*(days*1440))
        # Generate separately within split to avoid an episode crossing a split.
        events=[]
        eid=0
        start_pos=0
        for split_name,days in cfg["split_segments"]:
            segment_n=days*1440
            # 1 episode per calendar day (STRESS TEST; NOT FIELD INCIDENCE).
            for day in range(days):
                kind=str(rg.choice(EVENT_TYPES,p=EVENT_WEIGHTS))
                duration=int(rg.integers(40,181))
                # Place events only during intended operation, avoiding split boundary.
                onset=int(start_pos+day*1440+rg.integers(8*60,18*60))
                end=min(onset+duration,start_pos+segment_n-1)
                if kind=="diversion_to_pit":
                    severity=float(rg.uniform(.12,.38)); detail="fraction_of_condensed_mass_to_pit"
                elif kind=="return_pipe_loss":
                    severity=float(rg.uniform(.08,.27));detail="fraction_of_postflash_liquid_lost"
                elif kind=="trap_blowthrough":
                    severity=float(rg.uniform(.07,.24));detail="fraction_of_inlet_steam_blowthrough"
                elif kind=="return_meter_bias":
                    severity=float(rg.uniform(.08,.28));detail="fractional_underreading_of_liquid_return_meter"
                elif kind=="return_meter_dropout":
                    severity=1.;detail="sensor_reading_unavailable"
                elif kind=="transport_delay_shift":
                    severity=float(rg.uniform(1.8,3.3));detail="multiplier_on_receiver_tau"
                else:
                    severity=1.;detail="network_link_off"
                event_group="physical_loss" if kind in EVENT_TYPES[:3] else ("sensor_fault" if kind in EVENT_TYPES[3:5] else "nonloss_disturbance")
                eid+=1;event_id=f"{site}_{split_name}_E{eid:03d}"
                events.append((onset,end,kind,severity,event_id,event_group))
                episode_list.append(dict(site_id=site,split=split_name,event_id=event_id,event_type=kind,
                    event_group=event_group,start_timestamp=(START+timedelta(minutes=onset)).isoformat(),
                    end_timestamp_inclusive=(START+timedelta(minutes=end)).isoformat(),duration_min=end-onset+1,
                    severity=round(severity,6),severity_definition=detail,parameter_provenance="ASUMSI_SIMULASI_STRESS_TEST"))
            start_pos+=segment_n
        # Efficient lookup; non-overlap naturally due max duration < time between days.
        lookup={}
        for a,b,kind,sev,event_id,group in events:
            for k in range(a,b+1):
                assert k not in lookup, "synthetic episodes must not overlap"
                lookup[k]=(kind,sev,event_id,group)
        # Start with nominal equilibrium, but use a finite inventory state to model transport and startup.
        init_p=cfg["steam_pressure_setpoint_barg"]
        _,hf=sat_props(init_p)
        init_flash=max(0.0,(hf-HF_ATM)/HFG_ATM)
        inventory_kg=cfg["rated_steam_kg_h"]*0.07*(1-init_flash)*cfg["receiver_tau_min"]/60.0
        flow_memory=0.; sensor_memory_s=0.; sensor_memory_r=0.
        for idx in range(nrows):
            day=idx//1440;minute_day=idx%1440
            hour=minute_day/60.
            # Illustrative day pattern, NOT a textile mill shift log.
            if 6.0<=hour<6.5: mode="startup";load=0.12+0.78*(hour-6.0)/0.5
            elif 6.5<=hour<21.5: mode="production";load=0.77+0.14*np.sin(2*np.pi*(hour-6.5)/6.5)
            elif 21.5<=hour<22.: mode="shutdown";load=max(0.06,0.85-0.79*(hour-21.5)/0.5)
            else: mode="idle";load=0.07
            # Shift/day-to-day variability is a documented SCENARIO assumption.
            daily=1.0+0.05*np.sin(2*np.pi*(day%9)/9.)
            flow_memory=0.975*flow_memory+0.025*float(rg.normal(0.,0.065))
            fast_wobble=float(rg.normal(0.,0.007))
            throughput=float(np.clip(load*daily,0.,1.)) if mode=="production" else 0.0
            steam_rate=max(0.,cfg["rated_steam_kg_h"]*load*daily*(1+flow_memory+fast_wobble))
            # gauge pressure and saturation temperature used for STEAM model, not fabric temperature
            p_true=float(np.clip(cfg["steam_pressure_setpoint_barg"]+rg.normal(0.,0.08),0.,7.))
            t_sat,hf=sat_props(p_true)
            # Subcooling before depressurisation is a scenario setting 0..4 C.
            subcool=float(rg.uniform(0.,4.))
            flash_fraction=float(max(0.,(hf-HF_ATM-CP_WATER_APPROX*subcool)/HFG_ATM))
            event=lookup.get(idx)
            kind,sev,event_id,group=event if event else ("none",0.,"","normal")
            blow_rate=steam_rate*sev if kind=="trap_blowthrough" else 0.
            condense_rate=steam_rate-blow_rate
            flash_vent_rate=condense_rate*flash_fraction  # open receiver; vapor not counted as liquid return
            remaining_liquid=condense_rate-flash_vent_rate
            diverted_rate=remaining_liquid*sev if kind=="diversion_to_pit" else 0.
            liquid_after_diversion=remaining_liquid-diverted_rate
            pipeline_loss_rate=liquid_after_diversion*sev if kind=="return_pipe_loss" else 0.
            arrival_rate=liquid_after_diversion-pipeline_loss_rate
            tau=cfg["receiver_tau_min"]*(sev if kind=="transport_delay_shift" else 1.0)
            # exact discrete mass conservation: m_in = blowthrough+flash+divert+pipe_loss+return+dM/dt
            reservoir_before=inventory_kg+arrival_rate/60.
            release_kg=reservoir_before/(tau+1.)
            inventory_after=reservoir_before-release_kg
            true_return_rate=release_kg*60.
            dM_kg_min=inventory_after-inventory_kg
            residual_kg_min=(steam_rate-blow_rate-flash_vent_rate-diverted_rate-pipeline_loss_rate-true_return_rate)/60.-dM_kg_min
            assert abs(residual_kg_min)<1e-10, f"mass conservation violated: {site} {idx}: {residual_kg_min}"
            assert inventory_after>=-1e-10 and 0<=flash_fraction<0.20
            inventory_kg=inventory_after
            # Obvious diagnostic leakage trap: steam input and return are observed with *independent* noise.
            sensor_memory_s=0.90*sensor_memory_s+float(rg.normal(0.,0.0028))
            sensor_memory_r=0.92*sensor_memory_r+float(rg.normal(0.,0.0040))
            obs_steam=max(0.,steam_rate*(1+sensor_memory_s+rg.normal(0.,0.006)))
            obs_return=max(0.,true_return_rate*(1+sensor_memory_r+rg.normal(0.,0.010)))
            if kind=="return_meter_bias":obs_return*=1.-sev
            if kind=="return_meter_dropout":obs_return=None
            # all return temperatures below saturation at atmospheric receiver; independent measurement noise
            return_temp=float(np.clip(88.+2.5*np.tanh(steam_rate/cfg["rated_steam_kg_h"])+rg.normal(0,0.75),75.,98.))
            p_observed=float(np.clip(p_true+rg.normal(0.,0.025),0.,7.))
            steam_t_observed=float(t_sat+rg.normal(0.,0.45))
            online=0 if kind=="network_outage" else 1
            flag="return_meter_missing" if obs_return is None else ("gateway_offline_node_log_only" if not online else "observed")
            dt=(START+timedelta(minutes=idx)).isoformat()
            obs=dict(timestamp=dt,site_id=site,minute_id=idx,split=splits[idx],operating_mode=mode,
                     throughput_index=round(throughput,5),steam_flow_obs_kg_h=round(obs_steam,4),
                     condensate_return_obs_kg_h=round(obs_return,4) if obs_return is not None else "",
                     steam_pressure_obs_barg=round(p_observed,4),steam_temperature_obs_C=round(steam_t_observed,3),
                     return_temperature_obs_C=round(return_temp,3),link_online=online,data_quality_flag=flag)
            truth=dict(timestamp=dt,site_id=site,minute_id=idx,split=splits[idx],event_id=event_id,
                       event_type=kind,event_group=group,steam_in_true_kg_h=round(steam_rate,6),
                       condensate_return_true_kg_h=round(true_return_rate,6),
                       trap_blowthrough_true_kg_h=round(blow_rate,6),flash_vent_true_kg_h=round(flash_vent_rate,6),
                       divert_to_pit_true_kg_h=round(diverted_rate,6),return_line_loss_true_kg_h=round(pipeline_loss_rate,6),
                       hold_up_kg=round(inventory_kg,6),hold_up_change_kg_min=round(dM_kg_min,8),
                       flash_mass_fraction=round(flash_fraction,8),receiver_tau_active_min=round(tau,5),
                       liquid_evaporation_proxy_kg_h=round(condense_rate/cfg["kg_steam_per_kg_evaporated_liquid"],5))
            counts["rows"]+=1;counts[f"split_{splits[idx]}"]+=1;counts[f"event_min_{group}"]+=1
            yield obs,truth
        cfgstats[site]=dict(days=total_days,minute_rows=nrows,pressure_barg=cfg["steam_pressure_setpoint_barg"],
                            rated_steam_kg_h=cfg["rated_steam_kg_h"],tau_min=cfg["receiver_tau_min"],
                            sizing_dryer_type=cfg["sizing_dryer_type"],
                            kg_steam_per_kg_evaporated_liquid=cfg["kg_steam_per_kg_evaporated_liquid"],
                            n_episodes=len(events),start_synthetic=START.isoformat(),end_synthetic=(START+timedelta(minutes=nrows-1)).isoformat())
    return counts,cfgstats,episode_list

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def write_csv(p:Path,fieldnames:list[str],rows:list[dict]):
    with p.open("w",encoding="utf-8",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=fieldnames);wr.writeheader();wr.writerows(rows)

def generate(out:Path):
    out.mkdir(parents=True,exist_ok=True)
    sensor_path=out/"fluo_sensor_stream.csv.gz";truth_path=out/"fluo_physics_ground_truth.csv.gz"
    ep_path=out/"fluo_episode_labels.csv";config_path=out/"fluo_site_configs.csv"
    counts=Counter();cfgstats={};episodes=[]
    # streaming compressed records, no dense dataframe needed.
    with sensor_path.open("wb") as raw_s, truth_path.open("wb") as raw_t, \
         gzip.GzipFile(filename="",mode="wb",compresslevel=6,mtime=0,fileobj=raw_s) as g_s, \
         gzip.GzipFile(filename="",mode="wb",compresslevel=6,mtime=0,fileobj=raw_t) as g_t, \
         io.TextIOWrapper(g_s,encoding="utf-8",newline="") as so, \
         io.TextIOWrapper(g_t,encoding="utf-8",newline="") as to:
        sw=csv.DictWriter(so,fieldnames=SENSOR_FIELDS);tw=csv.DictWriter(to,fieldnames=TRUTH_FIELDS)
        sw.writeheader();tw.writeheader()
        for site_idx,cfg in enumerate(CONFIGS):
            pass
        # generator_rows has return value via StopIteration.value
        it=generator_rows()
        while True:
            try:obs,truth=next(it)
            except StopIteration as done:
                counts,cfgstats,episodes=done.value
                break
            sw.writerow(obs);tw.writerow(truth)
    write_csv(ep_path,list(EPISODE_FIELDS),episodes)
    write_csv(config_path,["site_id","rated_steam_kg_h","steam_pressure_setpoint_barg","receiver_tau_min","sizing_dryer_type","kg_steam_per_kg_evaporated_liquid","split_days","parameter_status"],
        [dict(site_id=c["site_id"],rated_steam_kg_h=c["rated_steam_kg_h"],steam_pressure_setpoint_barg=c["steam_pressure_setpoint_barg"],
              receiver_tau_min=c["receiver_tau_min"],sizing_dryer_type=c["sizing_dryer_type"],
              kg_steam_per_kg_evaporated_liquid=c["kg_steam_per_kg_evaporated_liquid"],split_days="; ".join(f"{name}:{days}" for name,days in c["split_segments"]),
              parameter_status="ASUMSI_SIMULASI_BUKAN_PABRIK") for c in CONFIGS])
    register=[
      ["KASUS NYATA","condensate discarded from sizing machine","qualitative","observed vendor case (not model parameter)","R1"],
      ["KASUS NYATA","17% annual fuel bill reduction","percent","vendor result, NOT used in simulation calibration","R1"],
      ["KASUS NYATA","87.8 m3/month less water used","m3/month","vendor result, NOT used in simulation calibration","R1"],
      ["LITERATUR","saturated steam at 3 barg: 144 C, hf 605","C;kJ/kg","published lookup","R2"],
      ["LITERATUR","saturated steam at 5 barg: 159 C, hf 671","C;kJ/kg","published lookup","R2"],
      ["LITERATUR","saturated steam at 7 barg: 170 C, hf 721","C;kJ/kg","published lookup","R2"],
      ["LITERATUR","0 barg hf 419 and hfg 2257","kJ/kg","published lookup","R2"],
      ["LITERATUR","7 barg, 250 kg/h illustrative example","barg;kg/h","worked example, NOT sizing plant measurement","R3"],
      ["METODE FISIKA","x_flash = max(0,(hf(up)-hf(0)-cp*subcool)/hfg(0))","ratio","energy balance and saturated steam flash","R3"],
      ["METODE FISIKA","m_steam=m_return + m_blowthrough + m_flash_vent + m_divert + m_pipe_loss + dM/dt","kg/h","control-volume mass conservation; dM/dt converted consistently","R4"],
      ["LITERATUR","two-cylinder sizing kg steam/kg evaporated liquid: min 1.6 avg 2.3 max 3.2","kg/kg","historical ATIRA survey via UNIDO monograph; NOT a measurement of Indonesian plant","R6"],
      ["LITERATUR","multi-cylinder sizing kg steam/kg evaporated liquid: min 1.5 avg 2.7 max 5.6","kg/kg","historical ATIRA survey via UNIDO monograph; NOT a measurement of Indonesian plant","R6"],
      ["METODE FISIKA","liquid evaporation PROXY = steam condensed / SEC scenario","kg/h","derived indicator, NOT measured evaporation or model feature","R6"],
      ["ASUMSI_SIMULASI","rated steam 200/250/300 by site","kg/h","sensitivity around 250 worked example; arbitrary scenario scaling","-"],
      ["ASUMSI_SIMULASI","receiver tau 4/7/11","min","unmeasured hydraulic residence times","-"],
      ["ASUMSI_SIMULASI","steam pressure 3/5/7","bar(g)","scenario points from steam table; NOT actual sizing values","R2"],
      ["ASUMSI_SIMULASI","startup 06:00, production 06:30-21:30, shutdown 21:30","clock WIB","artificial operating schedule, not plant log","-"],
      ["ASUMSI_SIMULASI","pressure noise SD 0.08, flow sensor noise 0.6%/1.0%","bar;fraction","instrument stress testing, NOT meter accuracy certificate","-"],
      ["ASUMSI_SIMULASI","one injected event per simulated day","events/day","stress-test prevalence only, NOT field failure rate","-"],
      ["ASUMSI_SIMULASI","event severity and duration distributions","fraction;min","chosen coverage, not validated incident statistics","-"],
      ["ASUMSI_SIMULASI","open atmospheric receiver, flashed vapour vented","-","specific model boundary, excludes flash condenser recovery","R3"],
      ["ASUMSI_SIMULASI","subcooling uniform 0-4 C","C","sensitivity only; not measured","R3"],
      ["ASUMSI_SIMULASI","return temperature centered ~88-91 C","C","model illustrative, NOT site thermometry","-"],
    ]
    write_csv(out/"fluo_parameter_provenance.csv",["classification","parameter_or_claim","unit","interpretation","source_id"],
        [dict(zip(["classification","parameter_or_claim","unit","interpretation","source_id"],row)) for row in register])
    manifest=dict(version=VERSION,seed=SEED,source_dates_as_of="2026-10-24",data_kind="FULLY_SYNTHETIC_NOT_FIELD_DATA",
       time_step_min=STEP_MIN,reference_example="7 bar(g), 250 kg/h from Spirax Sarco flash steam worked example, NOT textile mill",
       calibration_to_textile_case=False,site_specs_unknown=True,
       train_only="CFG_A and CFG_B train splits; evaluate on held-out temporal/configuration splits",
       event_prevalence="artificially enriched stress-testing; NOT a field failure rate",
       sizing_sec_basis="UNIDO Table 6 (original historical ATIRA surveys, 1970s publication) is kg steam per kg evaporated LIQUID, not yarn or fabric",
       evaporation_proxy_note="Calculated from modeled condensING steam and selected published SEC ratios; neither a measured throughput nor independent sensor",
       timestamp_semantics="illustrative calendar only, WIB; each site shares synthetic dates",
       sensor_file_sensor_only=True,truth_file_must_not_be_used_as_predictor=True,
       metadata_note="quality_status, return contamination and safe-to-recover are unknown; no valve actuation or ROI",
       counts=dict(counts),configs=cfgstats,n_episodes=len(episodes),episode_type_counts=dict(Counter(e["event_type"] for e in episodes)),
       source_references={
          "R1":"https://www.forbesmarshall.com/country-highlights-indonesia/optimising-energy-and-efficiency-at-a-textile-plant-in-western-indonesia/",
          "R2":"https://www.spiraxsarco.com/learn-about-steam/steam-engineering-principles-and-heat-transfer/what-is-steam",
          "R3":"https://www.spiraxsarco.com/learn-about-steam/condensate-recovery/flash-steam",
          "R4":"https://www.osti.gov/biblio/15000711",
          "R5":"https://www.energy.gov/cmei/femp/best-management-practice-8-steam-boiler-systems",
          "R6":"https://downloads.unido.org/ot/47/89/4789812/10001-15000_10251.pdf"},
       files={})
    for path in (sensor_path,truth_path,ep_path,config_path,out/"fluo_parameter_provenance.csv"):
        manifest["files"][path.name]={"size_bytes":path.stat().st_size,"sha256":sha(path)}
    (out/"fluo_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    return manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",default=".")
    a=ap.parse_args();m=generate(Path(a.out))
    print(json.dumps({"rows":m["counts"]["rows"],"episodes":m["n_episodes"],"splits":{k:v for k,v in m["counts"].items() if k.startswith("split_")},"data_status":m["data_kind"]},indent=2))
if __name__=="__main__":main()
