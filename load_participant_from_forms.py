import json
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = "https://swim.aadiyog.in/"

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

# --- Configuration ---
CSV_FILE_PATH = "/mnt/sda5/home/work/idsa-webapp/Inter School Swimming Competition 2026-27 (Responses) - Form Responses 1.csv"
EVENTS_JSON_PATH = "/mnt/sda5/home/work/idsa-webapp/events.json"

# Mapping from CSV column names to JSON schema fields
COLUMN_MAPPING = {
    "Column 6": "name",
    "Column 8": "dob",
    "Column 10": "age_group_text",  # Temporary for text, will convert to int
    "Column 7": "gender",
    "Column 3": "club",
    # "sfi_id" is nullable and not in CSV, will be None
}

# Mapping for age group text to integer
AGE_GROUP_MAP = {
    "Under - 15": 2,
    "Under -11": 3,  # Handling potential variations in spacing/hyphens
    "Under - 9": 4,
}

# Event columns in the CSV
EVENT_COLUMNS = ["Column 14", "Column 15", "Column 16"]


# --- Helper function to parse and format date ---
def format_dob(date_str):
    if pd.isna(date_str):
        return None
    try:
        # Attempt to parse with MM/DD/YYYY format
        date_obj = datetime.strptime(str(date_str), "%m/%d/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Fallback for DD/MM/YYYY format
            date_obj = datetime.strptime(str(date_str), "%d/%m/%Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print(
                f"Warning: Could not parse date string '{date_str}'. Returning None."
            )
            return None


# --- Helper Function to Load Events ---
def load_events(filepath):
    try:
        with open(filepath, "r") as f:
            events_data = json.load(f)

        # Create a dictionary for quick event lookup: (name, age_group_int, gender) -> id
        event_lookup = {}
        for event in events_data:
            # Normalize age group from JSON to match our integer mapping
            json_age_group_int = event["age_group"]

            # Find the corresponding integer age group from our map
            # We need to do this carefully as the json might use different numbers
            # For now, assuming direct match if possible, otherwise need more logic
            # Let's create a reverse map for the age group text to int first

            corresponding_age_group_int = None
            for text, num in AGE_GROUP_MAP.items():
                # This check is tricky: we need to ensure the event's age_group from JSON
                # aligns with the numerical age group we expect from the CSV.
                # For now, let's assume the event's age_group directly corresponds to our desired int.
                # e.g., if CSV has "Under - 15" -> 2, and JSON event has age_group: 2, it's a match.
                if (
                    event["age_group"] == num
                ):  # Direct match based on the numerical value
                    corresponding_age_group_int = num
                    break

            if corresponding_age_group_int is not None:
                key = (
                    event["name"],
                    corresponding_age_group_int,
                    event["gender"].lower(),
                )
                event_lookup[key] = event["id"]
        return event_lookup
    except FileNotFoundError:
        print(f"Error: Events file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
        return None


# --- Main Script Logic ---
def process_swimmer_data():
    event_lookup = load_events(EVENTS_JSON_PATH)
    if event_lookup is None:
        return

    try:
        df = pd.read_csv(CSV_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {CSV_FILE_PATH}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Rename columns based on mapping for easier access
    df.rename(columns=COLUMN_MAPPING, inplace=True)

    for index, row in df.iterrows():
        try:
            # --- Extract and Transform Data ---

            #
            #
            # ... other variable assignments

            name = row.get("name", "N/A")
            dob_raw = row.get("dob", None)  # Get the raw date string first
            dob_formatted = format_dob(
                dob_raw
            )  # Format it using our new function

            if dob_formatted is None:
                print(
                    f"Warning: Skipping {name} at row {index + 2} due to invalid or missing DOB."
                )
                continue  # Skip this row if DOB is critical and invalid

            gender_raw = row.get("gender", "Unknown")
            club = row.get("club", "Unknown")
            age_group_text = row.get("age_group_text", None)
            sfi_id = None  # Nullable, not present in CSV

            # Convert age group text to integer
            age_group_int = None
            if age_group_text in AGE_GROUP_MAP:
                age_group_int = AGE_GROUP_MAP[age_group_text]
            else:
                print(
                    f"Warning: Unknown age group text '{age_group_text}' for {name} at row {index + 2}. Skipping."
                )
                continue  # Skip this row if age group is not recognized

            # Normalize gender to lowercase for lookup
            gender = gender_raw.lower() if pd.notna(gender_raw) else "unknown"

            # --- Look up Event IDs ---
            event_ids = []
            for event_col in EVENT_COLUMNS:
                event_name = row.get(event_col, None)

                if pd.notna(event_name) and event_name.strip() != "None":
                    # Create lookup key: (event_name, age_group_int, gender)
                    event_key = (event_name.strip(), age_group_int, gender)

                    event_id = event_lookup.get(event_key)
                    if event_id:
                        event_ids.append(event_id)
                    else:
                        print(
                            f"Warning: Could not find event_id for '{event_name}' with age group {age_group_int} and gender '{gender}' for {name} at row {index + 2}."
                        )
                # If event_name is None or "None", we simply don't add an event_id for it.

            # --- Construct Payload ---
            payload = {
                "name": str(name) if pd.notna(name) else None,
                "dob": dob_formatted,
                "age_group": age_group_int,
                "gender": gender_raw
                if pd.notna(gender_raw)
                else None,  # Use raw gender for POST, if needed
                "club": str(club) if pd.notna(club) else None,
                "sfi_id": sfi_id,  # This will be None
                "event_id": event_ids,
            }

            # --- Send POST Request ---
            try:
                response = requests.post(DATABASE_URL, json=payload)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                print(
                    f"Successfully processed {name}. Status Code: {response.status_code}"
                )
            except requests.exceptions.RequestException as e:
                print(f"Error sending data for {name} at row {index + 2}: {e}")
                print(f"Payload: {payload}")

        except Exception as e:
            print(
                f"An unexpected error occurred processing row {index + 2}: {e}"
            )
            print(f"Row data: {row.to_dict()}")


# --- Execute the script ---
if __name__ == "__main__":
    process_swimmer_data()
