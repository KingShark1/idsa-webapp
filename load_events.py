import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Event

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./swimming_competition.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created
Base.metadata.create_all(engine)  # This line ensures all tables are created.

import csv
import json

def convert_csv_to_json(csv_file, json_file):
    events = []

    # Age group and gender mapping
    age_group_map = {
        "Senior": 0,
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4
    }
    gender_map = {
        "Men": "male",
        "Boys": "male",
        "Women": "female",
        "Girls": "female"
    }

    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            event = {
                "id": int(row["S.N."]),
                "name": row["Event Name"],
                "age_group": age_group_map.get(row["Group"], -1),
                "gender": gender_map.get(row["Category"], "unknown")
            }
            events.append(event)

    with open(json_file, 'w') as jsonfile:
        json.dump(events, jsonfile, indent=4)

# Usage


# Load events into the database
def load_events():
    db = SessionLocal()
    try:
        # Load events from JSON file
        with open("events.json", "r") as file:
            events = json.load(file)

        # Check if the event already exists to prevent duplicates
        new_events = [Event(id=e["id"], name=e["name"], age_group=e["age_group"], gender=e["gender"])
                      for e in events]

        db.add_all(new_events)
        db.commit()
        print(f"Loaded {len(new_events)} new events into the database.")

    finally:
        db.close()

if __name__ == "__main__":
    convert_csv_to_json('event_chart.csv', 'events.json')
    load_events()
