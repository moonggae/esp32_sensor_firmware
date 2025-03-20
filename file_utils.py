""" file_utils.py """
import uos

# ------------------------- CSV File Operations -------------------------

def create_file_if_not_exists(filename, headers=None):
    """Check if the file exists; if not, create it and add headers."""
    try:
        uos.stat(filename)  # Check if the file exists
    except OSError:
        with open(filename, "w") as file:
            if headers:
                file.write(",".join(headers) + "\n")  # Add headers
        print(f"Created new file: {filename}")

def append_to_file(filename, record):
    """Append new data to the CSV file."""
    try:
        with open(filename, "a") as file:
            file.write(",".join(map(str, record)) + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to append to {filename}: {e}")

def read_csv_file(filename):
    """Read a CSV file (excluding headers)."""
    try:
        with open(filename, "r") as file:
            lines = [line.strip() for line in file.readlines()]
            if len(lines) <= 1:
                print("No sensor data available.")
                return []
            return [line.split(",") for line in lines[1:]]  # Exclude headers
    except Exception as e:
        print(f"[ERROR] Failed to load {filename}: {e}")
        return []

def clear_file(filename, headers=None):
    """Clear the file content while keeping the headers (if provided)."""
    try:
        with open(filename, "w") as file:
            if headers:
                file.write(",".join(headers) + "\n")
        print(f"Cleared file: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to clear {filename}: {e}")

# ------------------------- Single Value File Operations (Name, MAC Address) -------------------------

def save_text_to_file(filename, data):
    """Save a single value (name, MAC address) to a file."""
    try:
        with open(filename, "w") as file:
            file.write(data)
        print(f"Saved to {filename}: {data}")
    except Exception as e:
        print(f"[ERROR] Failed to save {filename}: {e}")

def load_text_from_file(filename, default=None):
    """Load a single value (name, MAC address) from a file."""
    try:
        with open(filename, "r") as file:
            return file.read().strip()
    except OSError:
        return default
