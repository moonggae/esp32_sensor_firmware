""" rtc_manager.py """
from machine import RTC, deepsleep
import time

_DEEPSLEEP_DURATION_MS = 30 * 60 * 1000  #  30min

class RTCManager:
    def __init__(self):
        """Initialize RTCManager and RTC memory"""
        self.rtc = RTC()
        self.latest_time = None
        self.period = None
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
            latest_epoch, period_seconds = map(int, decoded_data.split(","))
            self.latest_time = latest_epoch
            self.period = period_seconds
            print(f"Loaded RTC Memory: Time={self.latest_time}, Period={self.period}")
        
        except (ValueError, AttributeError) as e:
            print(f"RTC Memory Load Error: {e}")
            self.latest_time, self.period = None, None  # Reset values to avoid further errors

    def save_rtc_memory(self, latest_epoch, period_seconds):
        """Save latest_time (epoch int) & period (seconds) directly to RTC memory"""
        try:
            rtc_data = f"{latest_epoch},{period_seconds}"
            self.rtc.memory(rtc_data.encode())  # Save to RTC memory
            self.latest_time = latest_epoch
            self.period = period_seconds
            print(f"✅ Saved RTC Memory: epoch={latest_epoch}, period={period_seconds} sec")
        except Exception as e:
            print(f"❌ RTC Memory Save Error: {e}")

    # ------------------------- set rtc -------------------------
    def set_rtc_datetime(self, epoch_time):
        """Set RTC time using epoch (Time Sync)"""
        try:
            tm = time.localtime(epoch_time)
            self.rtc.datetime((tm[0], tm[1], tm[2], 0, tm[3], tm[4], tm[5], 0))
            print(f"RTC Time Set: {epoch_time}")
        except Exception as e:
            print(f"RTC Time Set Error: {e}")
    
    def format_rtc_datetime(self):
        """Format RTC datetime to 'YYYY-MM-DDTHH:MM:SS'"""
        dt = self.rtc.datetime()
        return f"{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d}T{dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"

    def _current_epoch(self):
        dt = self.rtc.datetime()
        return time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], 0, 0))

    # ------------------------- check rtc time -------------------------
    def is_sensor_time(self):
        """Check if it's time to perform sensor measurement."""
        if self.latest_time is None or self.period is None:
            print("RTC wake time not set.")
            return False

        current_epoch = self._current_epoch()
        return current_epoch >= (self.latest_time + self.period)
    
    def is_advertise_time(self):
        """Check if wake-up occurred before next measurement time (early wake for advertise)."""
        if self.latest_time is None or self.period is None:
            return False

        current_epoch = self._current_epoch()
        return current_epoch < (self.latest_time + self.period)

    # ------------------------- deep sleep -------------------------
    def calculate_sleep_duration(self):
        """Calculate how long the ESP32 should stay in deep sleep (based on epoch time)"""
        dt = self.rtc.datetime()
        current_epoch_time = time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], 0, 0))
        next_wakeup_time = self.latest_time + self.period  

        remaining_seconds = next_wakeup_time - current_epoch_time
        remaining_ms = remaining_seconds * 1000

        if remaining_ms <= 0:
            print("🕒 측정 시간이 도달했거나 지남 → sleep 없음")
            return 0
        elif self.period >= _DEEPSLEEP_DURATION_MS // 1000:
            print(f"🛌 sensor period ≥ Deep sleep period → {_DEEPSLEEP_DURATION_MS // 1000} sec")
            return _DEEPSLEEP_DURATION_MS
        else:
            print(f"🛌 sensor period < Deep sleep period → {remaining_ms // 1000}sec")
            return remaining_ms

    def enter_deep_sleep(self):
        """Enter deep sleep mode for the required duration"""
        duration_ms = self.calculate_sleep_duration()
        if duration_ms <= 0:
            print("Wake-up time reached, no deep sleep needed.")
            deepsleep(10)
        print(f"Entering Deep Sleep for {duration_ms // 1000} sec...")
        deepsleep(duration_ms)
