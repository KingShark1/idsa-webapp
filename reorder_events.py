from models import Swimmer, SwimmerEvent, Event
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json


# Old database connection
SQLALCHEMY_DATABASE_URL_OLD = "sqlite:///./swimming_competition_old.db"
engine_old = create_engine(SQLALCHEMY_DATABASE_URL_OLD)
SessionLocalOld = sessionmaker(autocommit=False, autoflush=False, bind=engine_old)

# New database connection
SQLALCHEMY_DATABASE_URL_NEW = "sqlite:///./swimming_competition.db"
engine_new = create_engine(SQLALCHEMY_DATABASE_URL_NEW)
SessionLocalNew = sessionmaker(autocommit=False, autoflush=False, bind=engine_new)

def create_event_id_mapping(old_events_file, new_events_file):
    # Load old events from JSON file
    with open(old_events_file, "r") as file:
        old_events = json.load(file)

    # Load new events from JSON file
    with open(new_events_file, "r") as file:
        new_events = json.load(file)

    # Create a dictionary to map old event IDs to new event IDs
    old_to_new_id_map = {}

    # Create a lookup dictionary for new events based on event details
    new_events_lookup = {f"{event['name']} {event['gender']} {event['age_group']}": event['id'] for event in new_events}

    # Map old event IDs to new event IDs
    for old_event in old_events:
        key = f"{old_event['name']} {old_event['gender']} {old_event['age_group']}"
        new_event_id = new_events_lookup.get(key)
        if new_event_id is not None:
            old_to_new_id_map[old_event['id']] = new_event_id

    return old_to_new_id_map


def migrate_data(old_events_path, new_events_path):
    old_db = SessionLocalOld()
    new_db = SessionLocalNew()
    event_id_mapping = create_event_id_mapping(old_events_path, new_events_path)
    try:
        # Get all swimmers from the old database
        swimmers = old_db.query(Swimmer).all()
        print(len(swimmers))
        count = 0
        for swimmer in swimmers:
            # Create the swimmer in the new database
            new_swimmer = Swimmer(
                id=swimmer.id,
                name=swimmer.name,
                dob=swimmer.dob,
                sfi_id=swimmer.sfi_id,
                age_group=swimmer.age_group,
                gender=swimmer.gender,
                club=swimmer.club
            )
            new_db.add(new_swimmer)
            new_db.commit()

            # Get all SwimmerEvents for this swimmer
            swimmer_events = old_db.query(SwimmerEvent).filter(SwimmerEvent.swimmer_id == swimmer.id).all()

            for se in swimmer_events:
                # Map old event ID to new event ID
                new_event_id = event_id_mapping.get(se.event_id)
                if new_event_id:
                    # Create the SwimmerEvent in the new database
                    new_swimmer_event = SwimmerEvent(
                        swimmer_id=new_swimmer.id,
                        event_id=new_event_id,
                        medal=se.medal,
                        time=se.time,
                        lane_id=se.lane_id,
                        heat_id=se.heat_id
                    )
                    new_db.add(new_swimmer_event)

            new_db.commit()
            count += 1
            print(count)

        print("Data migration completed successfully.")

    finally:
        old_db.close()
        new_db.close()

# Run the data migration script
migrate_data("old_events.json", "events.json")

