""" rtc_manager.py """
from machine import RTC, deepsleep
import time

class RTCManager:
    def __init__(self):
        """Initialize RTCManager and RTC memory"""
        self.rtc = RTC()
        self.latest_time = None
        self.period = None
        self._load_rtc_memory()

    def _load_rtc_memory(self):
        """Load latest time & period from RTC memory"""
        try:
            rtc_data = self.rtc.memory()
            if rtc_data:
                latest_epoch, period_seconds = map(int, rtc_data.decode().split(","))
                self.latest_time = latest_epoch
                self.period = period_seconds
                print(f"Loaded RTC Memory: Time={self.epoch_to_iso(self.latest_time)}, Period={self.seconds_to_hms(self.period)}")
            else:
                print("RTC Memory is empty. Resetting values.")
                self.latest_time, self.period = None, None
        except Exception as e:
            print(f"RTC Memory Load Error: {e}")
            self.latest_time, self.period = None, None

    def save_rtc_memory(self, latest_time_str, period_str):
        """Save latest time (YYYY-MM-DDTHH:MM:SS) & period (HH:MM:SS) to RTC memory"""
        try:
            latest_epoch = self.iso_to_epoch(latest_time_str)
            period_seconds = self.hms_to_seconds(period_str)
            rtc_data = f"{latest_epoch},{period_seconds}"

            self.rtc.memory(rtc_data.encode())  # Save to RTC memory
            self.latest_time = latest_epoch
            self.period = period_seconds
            print(f"Saved RTC Memory: {latest_time_str}, Period={period_str}")
        except Exception as e:
            print(f"RTC Memory Save Error: {e}")

    def set_rtc_datetime(self, iso_time):
        """Set RTC time based on ISO 8601 (YYYY-MM-DDTHH:MM:SS) format"""
        try:
            epoch_time = self.iso_to_epoch(iso_time)
            tm = time.localtime(epoch_time)
            self.rtc.datetime((tm[0], tm[1], tm[2], 0, tm[3], tm[4], tm[5], 0))
            print(f"RTC Time Set: {iso_time} (Epoch: {epoch_time})")
        except Exception as e:
            print(f"RTC Time Set Error: {e}")

    def get_rtc_datetime(self):
        """Return the RTC datetime tuple (YYYY, MM, DD, weekday, HH, MM, SS, subseconds)"""
        return self.rtc.datetime()

    def format_rtc_datetime(self):
        """Format RTC datetime to 'YYYY-MM-DDTHH:MM:SS'"""
        dt = self.rtc.datetime()
        return f"{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d}T{dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"

    def check_wake_time(self):
        """Check if the current time (epoch) is past the next scheduled wake-up"""
        if self.latest_time is None or self.period is None:
            print("RTC wake time not set.")
            return False  # Wake time is not set

        current_epoch_time = self.iso_to_epoch(self.format_rtc_datetime())  # Convert current RTC time to epoch
        return current_epoch_time >= (self.latest_time + self.period)  # Compare epoch seconds

    def calculate_sleep_duration(self):
        """Calculate how long the ESP32 should stay in deep sleep (based on epoch time)"""
        if self.latest_time is None or self.period is None:
            print("RTC wake time not set. Defaulting to 60s sleep.")
            return 60000  # Default sleep time: 60 seconds

        current_epoch_time = self.iso_to_epoch(self.format_rtc_datetime())  # Convert current time to epoch
        next_wakeup_time = self.latest_time + self.period  # Next wake-up time (epoch)

        if current_epoch_time >= next_wakeup_time:
            print("Wake-up time has already passed, no deep sleep needed.")
            return 0  # Time has already passed → proceed immediately

        remaining_time = (next_wakeup_time - current_epoch_time) * 1000  # Convert to milliseconds
        print(f"Sleeping for {remaining_time // 1000} seconds until {self.epoch_to_iso(next_wakeup_time)}")
        return remaining_time

    def enter_deep_sleep(self):
        """Enter deep sleep mode for the required duration"""
        duration_ms = self.calculate_sleep_duration()
        if duration_ms <= 0:
            print("Wake-up time reached, no deep sleep needed.")
            return
        print(f"Entering Deep Sleep for {duration_ms // 1000} sec...")
        deepsleep(duration_ms)

    # ------------------------- Time Conversion Functions -------------------------

    def iso_to_epoch(self, iso_time):
        """Convert 'YYYY-MM-DDTHH:MM:SS' to epoch seconds"""
        try:
            tm = time.mktime((
                int(iso_time[:4]), int(iso_time[5:7]), int(iso_time[8:10]),  # YYYY-MM-DD
                int(iso_time[11:13]), int(iso_time[14:16]), int(iso_time[17:]),  # HH:MM:SS
                0, 0  # Weekday & yearday (ignored)
            ))
            return int(tm)
        except Exception as e:
            print(f"ISO to Epoch Conversion Error: {e}")
            return 0  # Return default value

    def epoch_to_iso(self, epoch_time):
        """Convert epoch seconds to 'YYYY-MM-DDTHH:MM:SS'"""
        tm = time.localtime(epoch_time)
        return f"{tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d}T{tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}"

    def hms_to_seconds(self, hms_time):
        """Convert 'HH:MM:SS' to total seconds"""
        try:
            h, m, s = map(int, hms_time.split(":"))
            return h * 3600 + m * 60 + s
        except Exception as e:
            print(f"HMS to Seconds Conversion Error: {e}")
            return 0  # Return default value

    def seconds_to_hms(self, seconds):
        """Convert total seconds to 'HH:MM:SS' format"""
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
