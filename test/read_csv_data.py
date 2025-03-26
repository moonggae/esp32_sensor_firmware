_DATA_FILE = "data.csv"

def read_csv_data():
    """📖 CSV 파일을 읽고 데이터를 리스트로 반환"""
    try:
        with open(_DATA_FILE, "r") as file:
            lines = file.readlines()  # 모든 줄을 읽음

        if len(lines) <= 1:
            print("⚠️ No sensor data available.")
            return []

        data_lines = lines[1:]  # 첫 줄(헤더) 제외
        parsed_data = [line.strip().split(",") for line in data_lines]  # 데이터 파싱
        print(f"✅ Read {len(parsed_data)} records from {_DATA_FILE}")
        return parsed_data

    except Exception as e:
        print(f"⚠️ Error reading {_DATA_FILE}: {e}")
        return []
    

csv_data = read_csv_data()
print(csv_data)