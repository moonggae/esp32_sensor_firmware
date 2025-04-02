""" rtc_manager.py """
from machine import RTC, deepsleep
import time

_DEEPSLEEP_DURATION_MS = 30 * 60 * 1000  #  30min

class RTCManager:
    def __init__(self):
        """Initialize RTCManager and RTC memory"""
        self.rtc = RTC()
        self.last_log_time = None
        self.log_period = None
        self.last_advertise_time = None
        self._load_rtc_memory()

    # ------------------------- rtc memory -------------------------
    def _load_rtc_memory(self):
        """Load latest time & period from RTC memory"""
        try:
            rtc_data = self.rtc.memory()
            if not rtc_data:
                print("RTC Memory is empty. Resetting values.")
                self.latest_time, self.period = None, None
                return

            decoded_data = rtc_data.decode().strip()
            if "," not in decoded_data:
                raise ValueError(f"Invalid RTC data format: {decoded_data}")
            
            latest_epoch, period_seconds, advertise_epoch = map(int, decoded_data.split(","))
            self.last_log_time = latest_epoch
            self.log_period = period_seconds
            self.last_advertise_time = advertise_epoch
            print(f"Loaded RTC Memory: Last Log Time={self.last_log_time}, Log Period={self.log_period}, Last Adv Time={self.last_advertise_time}")
        
        except (ValueError, AttributeError) as e:
            print(f"RTC Memory Load Error: {e}")
            self.latest_time, self.period = None, None  # Reset values to avoid further errors

    def save_rtc_memory(self, latest_epoch=None, period_seconds=None, advertise_time=None):
        """Save last_log_time (epoch int), log_period (seconds), and last_advertise_time to RTC memory."""
        try:
            latest_epoch = latest_epoch if latest_epoch is not None else self.last_log_time
            period_seconds = period_seconds if period_seconds is not None else self.log_period
            advertise_time = advertise_time if advertise_time is not None else self.last_advertise_time

            if latest_epoch is None or period_seconds is None or advertise_time is None:
                raise ValueError("All of latest_epoch, period_seconds, and advertise_time must be set.")

            rtc_data = f"{latest_epoch},{period_seconds},{advertise_time}"
            self.rtc.memory(rtc_data.encode())  # Save to RTC memory

            self.last_log_time = latest_epoch
            self.log_period = period_seconds
            self.last_advertise_time = advertise_time

            print(f"✅ Saved RTC Memory: log_time={latest_epoch}, log_period={period_seconds}, last_adv={advertise_time}")
        except Exception as e:
            print(f"❌ RTC Memory Save Error: {e}")

    # ------------------------- set rtc -------------------------
    def set_rtc_datetime(self, time_list):
        """Set RTC time using [YYYY, MM, DD, HH, MM, SS] format"""
        try:
            if len(time_list) != 6:
                raise ValueError("Invalid time format. Expected [YYYY, MM, DD, HH, MM, SS]")
            
            year, month, day, hour, minute, second = time_list

            self.rtc.datetime((year, month, day, 0, hour, minute, second, 0))
            print(f"✅ RTC Time Set: {time_list}")

            return time.mktime((year, month, day, hour, minute, second, 0, 0))

        except Exception as e:
            print(f"RTC Time Set Error: {e}")
    
    def format_rtc_datetime(self):
        """Format RTC datetime to 'YYYY-MM-DDTHH:MM:SS'"""
        dt = self.rtc.datetime()
        return f"{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d}T{dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"

    # ------------------------- check rtc time -------------------------

    def current_epoch(self):
        dt = self.rtc.datetime()
        return time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], 0, 0))

    def is_sensor_time(self):
        """Check if it's time to perform sensor measurement."""
        if self.last_log_time is None or self.log_period is None:
            print("RTC wake time not set.")
            return False

        current_epoch = self.current_epoch()
        return current_epoch >= (self.last_log_time + self.log_period)
    
    def is_advertise_time(self):
        """Check if the advertising period has passed since the last advertisement."""
        if self.last_advertise_time is None:
            return False

        current_epoch = self.current_epoch()
        elapsed = current_epoch - self.last_advertise_time

        return elapsed >= (_DEEPSLEEP_DURATION_MS // 1000)

    # ------------------------- deep sleep -------------------------
    def calculate_sleep_duration(self):
        """Calculate how long the ESP32 should stay in deep sleep (based on epoch time)"""
        dt = self.rtc.datetime()
        current_epoch_time = time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], 0, 0))

        next_wakeup_time = self.last_log_time + self.log_period
        remaining_seconds = next_wakeup_time - current_epoch_time
        remaining_ms = remaining_seconds * 1000

        if remaining_ms <= 0:
            print("Wake-up time reached, no deep sleep needed.")
            return 0
        elif self.log_period >= _DEEPSLEEP_DURATION_MS // 1000:
            print(f"🛌 Log period ≥ Deep sleep period → {_DEEPSLEEP_DURATION_MS // 1000} sec")
            return _DEEPSLEEP_DURATION_MS
        else:
            print(f"🛌 Log period < Deep sleep period → {remaining_ms // 1000}sec")
            return remaining_ms

    def enter_deep_sleep(self):
        """Enter deep sleep mode for the required duration"""
        duration_ms = self.calculate_sleep_duration()
        if duration_ms <= 0:
            deepsleep(10)
        print(f"Entering Deep Sleep for {duration_ms // 1000} sec...")
        deepsleep(duration_ms)