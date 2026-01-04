import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# --- Restaurant Configuration ---
MAX_CAPACITY = 20 # Maximum number of people at any given time

# Restaurant opening hours
OPENING_HOURS = {
    "weekday": { # Monday, Wednesday, Thursday, Friday
        "lunch": {"start": 12, "end": 15},
        "dinner": {"start": 19, "end": 23},
    },
    "tuesday": None, # Tuesday is closed
    "weekend": { # Saturday and Sunday
        "lunch": {"start": 12, "end": 15},
        "dinner": {"start": 19, "end": 23},
    },
}

# Last time a reservation can be made
LAST_RESERVATION_TIME_LUNCH = {"hour": 14, "minute": 30}
LAST_RESERVATION_TIME_DINNER = {"hour": 21, "minute": 30}


# --- Session Management ---
SESSION_TTL = timedelta(seconds=int(os.environ.get("SESSION_TTL", 3600)))
