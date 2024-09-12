import pandas as pd
import requests
import os
from sqlalchemy.orm import Session
from models import Event
from database import engine, SessionLocal
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm
# Load the Excel file
file_path = 'CBSE entry data clean list .xlsx'  # Update with your actual path
df = pd.read_excel(file_path)

# Start a session with the database
session = SessionLocal()

# Fetch all event IDs from the database
event_mapping = {}
events = session.query(Event).all()
for event in events:
    event_mapping[event.name.lower()] = event.id

# Close the session after fetching event IDs
session.close()

# Custom filter to format date
def format_date(value, format="%Y-%m-%d"):
    if isinstance(value, str):
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return date_obj.strftime(format)
        except:
            date_obj = datetime.strptime(value, "%d-%m-%Y")
            return date_obj.strftime(format)
    return value

# Dictionary to aggregate swimmer data
swimmers = defaultdict(lambda: {
    'name': None,
    'dob': None,
    'age_group': None,
    'gender': None,
    'club': None,
    'sfi_id': None,
    'event_id': [],
    'event_names': [],
    'total_events': None
})

age_group_map = {
    "Under 19": 1,
    "Under 17": 2,
    "Under 14": 3,
    "Under 11": 4,
}

# Constraints for the number of events (excluding relays) by age group
event_constraints = {
    1: 5,  # Under 19
    2: 5,  # Under 17
    3: 4,  # Under 14
    4: 3   # Under 11
}

# Function to log duplicate participants in an event
duplicate_log_file = "duplicate_participants.xlsx"

def log_duplicate_participants(event_name, event_id, club, participants):
    # Check if the log file exists
    if os.path.exists(duplicate_log_file):
        df = pd.read_excel(duplicate_log_file)
    else:
        # If the file doesn't exist, create an empty DataFrame
        df = pd.DataFrame(columns=["Event Name", "Event ID", "School", "Participants"])

    # Create a new row for the duplicated participants
    new_row = {"Event Name": event_name, "Event ID": event_id, "School": club, "Participants": ", ".join(participants)}
    df = df._append(new_row, ignore_index=True)

    # Write back to the Excel file
    df.to_excel(duplicate_log_file, index=False)

log_file = "swimmer_assertions.xlsx"

# Function to log errors into an Excel file
def log_error(swimmer_name, event_name, club, reason):
    # Check if the log file exists
    if os.path.exists(log_file):
        # Read the existing file
        df = pd.read_excel(log_file)
    else:
        # If the file doesn't exist, create an empty DataFrame
        df = pd.DataFrame(columns=["Swimmer", "Event", "Club", "Reason"])
    
    # Append the new error as a new row
    new_row = {"Swimmer": swimmer_name, "Event": event_name, "Club": club, "Reason": reason}
    df = df._append(new_row, ignore_index=True)

    # Write back to the Excel file
    df.to_excel(log_file, index=False)

# Iterate over each row in the dataframe to populate the swimmers dictionary
for _, row in df.iterrows():
    # Extract necessary data
    student_name = row['studentname']  # Replace with actual column name
    dob = format_date(row['dob'])  # Replace with actual column name
    age_group = age_group_map[row['agegroup']]  # Replace with actual column name
    gender = row['gender'].lower()  # Replace with actual column name
    club = row['SchoolName']  # Replace with actual column name
    sfi_id = str(row.get('affno', None))  # Optional field, replace with actual column name
    event_name = row['gametype']  # Replace with actual column name

    # Generate a key for the swimmer
    swimmer_key = (student_name, dob, gender, club)

    # Populate the swimmer data if it's not already set
    if swimmers[swimmer_key]['name'] is None:
        swimmers[swimmer_key]['name'] = student_name
        swimmers[swimmer_key]['dob'] = dob
        swimmers[swimmer_key]['age_group'] = age_group
        swimmers[swimmer_key]['gender'] = gender
        swimmers[swimmer_key]['club'] = club
        swimmers[swimmer_key]['sfi_id'] = sfi_id
        swimmers[swimmer_key]['total_events'] = 0
        swimmers[swimmer_key]['event_names'] = []

    # Check if the event is a relay (if relay is part of the event name)
    is_relay = 'relay' in event_name.lower()

    # Skip relays for event count validation
    if not is_relay:
        swimmers[swimmer_key]['total_events'] += 1


    # Find the correct event_id based on name, age_group, and gender
    matching_event, matchin_name = next(
        ((event.id, event.name) for event in events 
         if event.name == event_name 
         and event.age_group == age_group 
         and event.gender.lower() == gender.lower()), 
        (None, None)
    )

    if matching_event:
        swimmers[swimmer_key]['event_id'].append(matching_event)
        swimmers[swimmer_key]['event_names'].append(matchin_name)
    else:
        log_error(student_name, event_name, club, f"No matching event found for age group, gender '{event_name}'")

# Second Pass: Check if there are multiple participants from the same school in the same event
event_participants_by_school = defaultdict(lambda: defaultdict(list))

# Aggregate participants by event and school
for swimmer_key, swimmer_data in swimmers.items():
    if swimmer_data['total_events'] > event_constraints[swimmer_data['age_group']]:
        log_error(swimmer_data['name'], 
                  swimmer_data['event_names'], 
                  swimmer_data['club'], 
                  f"Exceeded max ({event_constraints[swimmer_data['age_group']]}) allowed events")
        continue
    for event_id in swimmer_data['event_id']:
        event_name = next((event.name for event in events if event.id == event_id), None)
        event_participants_by_school[event_id][swimmer_data['club']].append(swimmer_data['name'])

# Check for violations (multiple participants from the same school in the same event)
for event_id, school_participants in event_participants_by_school.items():
    for school, participants in school_participants.items():
        if len(participants) > 1:  # More than 1 participant from the same school
            event_name = next((event.name for event in events if event.id == event_id), None)
            log_duplicate_participants(event_name, event_id, school, participants)
            
# Define the API endpoint
api_url =  'http://127.0.0.1:8000' # Replace with your actual API URL

# Send data to the "/" endpoint
for swimmer_key, swimmer_data in tqdm(swimmers.items(), total=len(swimmers.items()), desc="Processing Swimmers"):
    response = requests.post(api_url, json=swimmer_data)
    if response.status_code != 200:
        # print(f"Failed to register swimmer {swimmer_data['name']}: {response.text}")
        print(f"failed to register swimmer : {swimmer_data['name']}") 

print("Data processing and submission complete.")
