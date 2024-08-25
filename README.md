# Load events needs to be run seperately from the main.py

Post request for submitting an entry
{"name":"King Shark","dob":"0001-11-20","age_group":"0","gender":"Male","club":"IDSA","sfi_id":"","event_id[]":"62","event_id":["41","51","62"]}


For recalculating all the heat and lane ID's : curl -X POST "http://localhost:8000/recalculate_heats_lanes/{event_id}"