# WMM

Streamlit dashboard for exploring Indonesian runners in the World Marathon Majors dataset.

Live app: https://wmm-id.streamlit.app/

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

## Live Deployment

- Streamlit Community Cloud: https://wmm-id.streamlit.app/
