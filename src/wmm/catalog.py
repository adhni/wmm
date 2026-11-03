"""The races covered by this app, independent of available result rows."""
from __future__ import annotations

RACES = {
    "Berlin": {"color": "#b33f24", "start_year": 2012, "source": "https://www.bmw-berlin-marathon.com/en/your-race/results"},
    "Boston": {"color": "#ce7f3c", "start_year": 2012, "source": "https://www.baa.org/races/boston-marathon/results/"},
    "Chicago": {"color": "#164b63", "start_year": 2012, "source": "https://www.chicagomarathon.com/results/"},
    "London": {"color": "#638d8b", "start_year": 2012, "source": "https://www.londonmarathonevents.co.uk/london-marathon/results"},
    "NYC": {"color": "#221f3b", "start_year": 2012, "source": "https://prod.nyrr.org/tcsnycmarathon/race-results"},
    "Tokyo": {"color": "#8654a0", "start_year": 2013, "source": "https://www.marathon.tokyo/en/about/past/"},
    "Sydney": {"color": "#25856b", "start_year": 2025, "source": "https://www.tcssydneymarathon.com/past-results"},
}
SIX_STAR = ("Tokyo", "Boston", "London", "Berlin", "Chicago", "NYC")
SEVEN_RACES = tuple(RACES)
JOURNEYS = {"Original Six": SIX_STAR, "Seven races covered": SEVEN_RACES}
TARGET_YEAR = 2026
