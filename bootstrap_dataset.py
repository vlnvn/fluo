#!/usr/bin/env python3
"""Extract the checked-in synthetic-only v1 data package to data/original."""
from pathlib import Path
from zipfile import ZipFile

BASE=Path(__file__).resolve().parent
ARCHIVE=BASE/'datasets'/'FLUO_DEEPX_SYNTHETIC_DATASET_V1_20261024.zip'
OUT=BASE/'data'/'original'
FILES={'fluo_sensor_stream.csv.gz','fluo_physics_ground_truth.csv.gz','fluo_episode_labels.csv','fluo_manifest.json','fluo_parameter_provenance.csv','fluo_site_configs.csv'}

def main():
    if not ARCHIVE.is_file():
        from generate_fluo import generate
        OUT.mkdir(parents=True,exist_ok=True)
        generate(OUT)
        print('Generated synthetic data from the checked-in generator:', OUT)
        return
    OUT.mkdir(parents=True,exist_ok=True)
    with ZipFile(ARCHIVE) as archive:
        seen=set()
        for info in archive.infolist():
            name=Path(info.filename).name
            if name not in FILES:continue
            if name in seen:raise ValueError('Duplicate dataset member: '+name)
            seen.add(name)
            data=archive.read(info)
            (OUT/name).write_bytes(data)
    if seen!=FILES:raise ValueError('Missing data members: '+str(sorted(FILES-seen)))
    print('Extracted',len(seen),'files into',OUT)

if __name__=='__main__':main()
