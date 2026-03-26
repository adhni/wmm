# WMM

Streamlit dashboard for exploring Indonesian runners in the World Marathon Majors dataset.

## Data

- `raw_data.csv`: source data copied from the original `posts/WMM` project
- Columns: `Marathon`, `Year`, `Name`, `Time`, `Place`

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Current Dashboard

- Filter by marathon and year range
- Track participation pulse, latest-year snapshots, and rank drift
- Explore `Road to Stars` progress and one-away runners
- Browse `Hall of Fame` badges and leaderboards
- View marathon-specific profiles and finish-time fingerprints
- Search runner journeys, milestones, Indo ranks, and course mix
- Download filtered data, stars tables, and runner logs

## Project Layout

- `app.py`: Streamlit app entrypoint
- `src/wmm/data.py`: data loading and time formatting
- `src/wmm/metrics.py`: reusable analysis tables for the dashboard
- `.streamlit/config.toml`: Streamlit theme and server config

## Deploy To Streamlit Community Cloud

According to the current official Streamlit docs, Community Cloud deploys directly from a GitHub repository. You choose the repository, branch, and entrypoint file, and Community Cloud runs the app from the repo root. It also supports selecting a Python version in Advanced settings, and currently defaults to Python 3.12.

Recommended setup for this repo:

- Repository root contains `requirements.txt`
- Entrypoint file is `app.py`
- Streamlit config is in `.streamlit/config.toml`

Deployment steps:

1. Push this repo to GitHub.
2. Sign in to Streamlit Community Cloud and connect GitHub.
3. Click `Create app`.
4. Select this repository and branch.
5. Set the entrypoint file to `app.py`.
6. Optionally choose a custom subdomain.
7. In Advanced settings, confirm the Python version if needed.
8. Deploy.

Official docs used:

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
