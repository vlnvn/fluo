# Getting started

Choose the path matching what you want to evaluate.

## A. Explore the hosted prototype

1. Ask the repository maintainer for an **authorized Vercel reviewer link**. The plain [preview URL](https://fluo-o3h0wtwma-vlnvns-projects.vercel.app) remains provider-protected.
2. Open the link. Start a private guest workspace; it expires after approximately two hours and is not a named operator account.
3. Open **Overview** to see current steam/return readings and model context.
4. Switch to **Scenario Review**, reset the replay and select **Return diversion**. Start playback and revisit Overview to inspect changes as the cursor advances.
5. Open **Event Center**, inspect a warning, record a review step and generate an event PDF.
6. Compare **Return meter bias** and **Connection outage**. Neither case permits an automatic recovery conclusion.

The observations use simulated telemetry for a fictional facility; no factory equipment is connected. The maintainer may revoke the share capability.

## B. Explore the research source on main

Prerequisites: a supported local Python environment and the source-controlled Python dependencies. This branch contains the research scripts, not the React/FastAPI workspace.

```sh
git clone https://github.com/vlnvn/fluo.git
cd fluo
python -m venv .venv
# Activate the venv for your shell before installing.
python -m pip install -r requirements.txt
python bootstrap_dataset.py
```

For the full frozen research reproduction, follow the existing stage sequence:

```sh
python prepare_cohorts.py
python compare_models.py
python generate_final_holdout.py
python final_validation.py
python run_fluo_v2.py
python qa_and_demo.py
python robustness_stress.py
```

The historical run has specific archived inputs and a frozen selected model. **A fresh clone alone does not contain all private research artifacts needed to reproduce the audited application release.** Do not interpret an unverified rerun as the published results.

## C. Run the application locally (authorized archive required)

Use the [application branch](https://github.com/vlnvn/fluo/tree/deploy/vercel-hobby) with its existing setup scripts. The documented local workflow assumes **Windows PowerShell**, Python **3.12/3.13**, Node.js **22.12+**, npm and the audited `FLUO_ML_RESEARCH_AUDITED_20261024.zip` obtained from the authorized project workspace.

```powershell
git checkout deploy/vercel-hobby
.\setup.ps1
.\.venv\Scripts\python.exe tools\dev.py
```

Open `http://127.0.0.1:5173` after the launcher reports readiness. This is loopback development, not the cloud preview. The setup validates archive/model hashes and does **not** retrain the frozen model.

For reproducible tests, deployment configuration and failure modes, use the [application README](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/README.md) and the [Vercel runbook](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/deployment/VERCEL_RELEASE_RUNBOOK.md). Cloud provisioning requires separately approved credentials and private research artifacts; do not copy them into source control.

[Back to documentation index](README.md).
