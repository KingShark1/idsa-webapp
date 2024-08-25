# import requests
# import pprint

# data= {"name":"Manas","dob":"2001-11-20","age_group":"2","gender":"Male","club":"IDSA","sfi_id":"","event_id":["3","4"]}
# r = requests.post("http://localhost:8000", json=data)
# print(r.status_code)

# pprint.pprint(r.json())

import json
import requests
import pprint
from datetime import datetime

# Load the events.json
with open('events.json', 'r') as f:
    events = json.load(f)

event_mapping = {
    "50m FS": "50 mt. Free Style",
    "100m FS": "100 mt. Free Style",
    "200m FS": "200 mt. Free Style",
    "400m FS": "400 mt. Free Style",
    "800m FS": "800 mt. Free Style",
    "1500m FS": "1500 mt. Free Style",
    "50m BK": "50 mt. Back Stroke",
    "100m BK": "100 mt. Back Stroke",
    "200m BK": "200 mt. Back Stroke",
    "50m BR": "50 mt. Breast Stroke",
    "100m BR": "100 mt. Breast Stroke",
    "200m BR": "200 mt. Breast Stroke",
    "50m Fly": "50 mt. Butterfly Stroke",
    "100m Fly": "100 mt. Butterfly Stroke",
    "200m Fly": "200 mt. Butterfly Stroke",
    "200m IM": "200 mt. Individual Medley",
    "400m IM": "400 mt. Individual Medley",
    # Add other mappings as needed
}


# Define the swimmer data (you can load this from a file or another source as needed)
swimmer_data = """
Abeer Singh Mehta	01-02-2007	0	SFIMAXXMP12328	Male	50m FS	100m FS	50m BK	50m Fly	50m BR
Sarah Wilson	11-03-2009	0	SFIFAXXMP12337	Female	800m FS	400m FS	200m BK	200m IM	400m IM
Manaswini Thatte	06-04-2009	0	SFIFAXXMP12290	Female	50m Breast	100m Breast	200m Breast	200m IM	50m FS
Abeer Singh Mehta	01-02-2007	1	SFIMAXXMP12328	Male	50m FS	100m FS	50m BK	50m Fly	50m BR
Jyotiraditya Namil	12-04-2007	1		Male	100m FS	50m BR	100m Breast	50m BK	
Darshita Kashliwal	23-01-2007	1		Female	50m BK	100m BK	200m BK		
Jalaj Kasbe	09-10-2008	1		Male	200m Fly	100m Fly	400m FS	1500m FS	200m IM
Sarah Wilson	11-03-2009	1	SFIFAXXMP12337	Female	800m FS	400m FS	200m BK	200m IM	400m IM
Manaswini Thatte	06-04-2009	1	SFIFAXXMP12290	Female	50m Breast	100m Breast	200m Breast	200m IM	50m FS
Prajjwal Nagpal	04-04-2009	1		Male	200m FS	200m Fly	400m FS		
Shounit Jain	15-10-2008	1		Male	50m FS	50m Breast	50m BK	100m Breast	100m BK
Shourya Sojatia	01-05-2009	1		Female	50m Fly	100m Fly	400m FS	50m FS	
Kshaunish Satsangi	01-04-2011	1		Male	50m FS	100m FS	50m Fly	100m Fly	200m IM
Yagyeash Narayan	23-07-2007	1		Male	50m Breast	100m Breast	50m FS		
Varchasva Choudhary	06-02-2010	2		Male	50m BK	100m BK	50m FS	200m BK	
Rajvee Chugh	19-07-2010	2		Female	50m BR	100m BR	200m BR		
Anshika Mittal	21-08-2012	2		Female	50m BR	100m FS	100m BR	50m FS	
Joy Choudhary	15-09-2011	2		Male	50m FS	100m FS	200m FS		
Aarav Jhaveri	23-01-2010	2		Male	400m FS	200m FS	50m FLY	50m BK	100m BK
Heer Baherwani	23-09-2011	2	SFIFAXXMP23349	Female	50m FS	50m Fly	100m Fly	200m Fly	200m FS
Meher Singh Neekhra	16-09-2010	2		Male	200m FS	100m FS	50m BR	100m BR	
Rupal Pandya	16-10-2012	2		Female	100m FS	50m FS	50m BR		
Vedika Toshniwal	16-01-2011	2		Female	50m BK	100m FS	50m BR	100m BK	
Ruchir Thatte	03-02-2013	3		Male	50m FS	50m BK	50m Fly	100m BR	200m IM
Udit Parkhe	03-04-2014	3		Male	50m Fly	100m FS	50m BR	50m FS	200m IM
Daniyal Nadeem	23-03-2016	4		Male	50m BR	50m FS	100m FS	50m Fly	200m IM
"""

def convert_date_format(date_str):
    # Parse the date from the original format
    original_date = datetime.strptime(date_str, '%d-%m-%Y')
    # Convert the date to the desired format
    formatted_date = original_date.strftime('%Y-%m-%d')
    return formatted_date

# Parse the swimmer data
swimmers = []
current_swimmer = {}
for line in swimmer_data.split('\n'):
    if not line.strip():
        continue
    parts = line.split('\t')
    if len(parts) >= 6:
        if current_swimmer:
            swimmers.append(current_swimmer)
        current_swimmer = {
            "name": parts[0],
            "dob": parts[1],
            "age_group": int(parts[2]),
            "sfi_id": parts[3],
            "gender": parts[4],
            "events": parts[5:]
        }
    else:
        current_swimmer["events"].extend(parts)

if current_swimmer:
    swimmers.append(current_swimmer)

def normalize_event_name(event_name, mapping):
    # Convert to a common format
    for short_form, full_form in mapping.items():
        if event_name in [short_form, full_form]:
            return full_form
    return event_name

def find_event_ids(event_names, age_group, gender, events, mapping):
    event_ids = []
    for event_name in event_names:
        normalized_event_name = normalize_event_name(event_name, mapping)
        for event in events:
            if normalize_event_name(event['name'], mapping) == normalized_event_name and event['age_group'] == age_group and event['gender'].lower() == gender.lower():
                event_ids.append(event['id'])
                break
    return event_ids

for swimmer in swimmers:
    event_ids = find_event_ids(swimmer['events'], swimmer['age_group'], swimmer['gender'], events, event_mapping)
    print(event_ids)

# Prepare and send POST requests
for swimmer in swimmers:
    event_ids = find_event_ids(swimmer['events'], swimmer['age_group'], swimmer['gender'], events, event_mapping)
    post_data = {
        "name": swimmer["name"],
        "dob": convert_date_format(swimmer["dob"]),
        "age_group": swimmer["age_group"],
        "gender": swimmer["gender"],
        "club": "Daly College",
        "sfi_id": swimmer["sfi_id"],
        "event_id[]": event_ids,
        "event_id": event_ids
    }
    response = requests.post('http://localhost:8000', json=post_data)
    print(f'Status Code: {response.status_code}')
