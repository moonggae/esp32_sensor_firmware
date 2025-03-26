""" file_utils.py """
import uos

_DATA_FILE = "data.csv"
_DATA_HEADER = ["t", "tp", "hd"]

# ------------------------- CSV File Operations -------------------------

def create_file_if_not_exists():
    """Check if the file exists; if not, create it and add headers."""
    try:
        uos.stat(_DATA_FILE)  # Check if the file exists
    except OSError:
        with open(_DATA_FILE, "w") as file:
            file.write(",".join(_DATA_HEADER) + "\n")  # Add headers
        print(f"Created new file: {_DATA_FILE}")

def append_to_file(record):
    """Append new data to the CSV file."""
    try:
        with open(_DATA_FILE, "a") as file:
            file.write(",".join(map(str, record)) + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to append to {_DATA_FILE}: {e}")

def read_csv_file():
    """Read a CSV file (excluding headers)."""
    try:
        with open(_DATA_FILE, "r") as file:
            lines = [line.strip() for line in file.readlines()]
            if len(lines) <= 1:
                print("No sensor data available.")
                return []
            return [line.split(",") for line in lines[1:]]  # Exclude headers
    except Exception as e:
        print(f"[ERROR] Failed to load {_DATA_FILE}: {e}")
        return []

def clear_data_file():
    """Clear the file content while keeping the headers (if provided)."""
    try:
        with open(_DATA_FILE, "w") as file:
            file.write(",".join(_DATA_HEADER) + "\n")
        print(f"Cleared file: {_DATA_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to clear {_DATA_FILE}: {e}")
