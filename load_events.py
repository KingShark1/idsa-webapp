import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Event
import os

# Database setup
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:ErmWsGnksaBwaCWStClxMdAhUTAFILmP@postgres.railway.internal:5432/railway")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created
Base.metadata.create_all(engine)  # This line ensures all tables are created.

import csv
import json

def convert_csv_to_json(csv_file, json_file):
    events = []

    with open('static/config.json', 'r') as config_file:
        config = json.load(config_file)

    assert "age_group_map" in config
    assert "gender_map" in config
    assert "time_trial_map" in config

    # Age group and gender mapping

    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            event = {
                "id": int(row["Event No"]),
                "name": row["Event"],
                "age_group": config["age_group_map"].get(row["Age Group"], -1),
                "gender": config["gender_map"].get(row["Gender"], "unknown"),
                "time_trial": config["time_trial_map"].get(row["Mode"], 1)

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
        new_events = [Event(id=e["id"], name=e["name"], age_group=e["age_group"], gender=e["gender"], time_trial=e["time_trial"])
                      for e in events]

        db.add_all(new_events)
        db.commit()
        print(f"Loaded {len(new_events)} new events into the database.")

    finally:
        db.close()

if __name__ == "__main__":
    convert_csv_to_json('CBSE West Zone 2024 - EventChart.csv', 'events.json')
    load_events()
