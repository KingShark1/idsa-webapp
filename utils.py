import json
from datetime import datetime


lane_order = [4, 5, 3, 6, 2, 7, 1, 8]


def load_json(file_path: str):
    with open(file_path, 'r') as file:
        events = json.load(file)
    return events

def convert_time_to_total_ms(time_str):
    """Convert time string (mm:ss:ms) to total milliseconds."""
    if not time_str:
        return float('inf')  # Treat missing times as infinitely large
    if time_str == "":
        return float('inf')
    minutes, seconds, milliseconds = map(int, time_str.split(':'))
    total_ms = (minutes * 60 * 100) + (seconds * 100) + milliseconds
    return total_ms

# Custom filter to format date
def format_date(value, format="%d-%m-%Y"):
    if isinstance(value, str):
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return date_obj.strftime(format)
        except:
            date_obj = datetime.strptime(value, "%Y-%m-%d")
            return date_obj.strftime(format)
    return value