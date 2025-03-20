# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
#import webrepl
#webrepl.start()

import uasyncio as asyncio
import machine
import esp32
from rtc_manager import RTCManager
from aioble_manager import BLEManager
from sensor_logger import SensorLogger

# boot 버튼을 esp32.wake_on_ext0로 설정
boot_button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP) 
esp32.wake_on_ext0(pin=boot_button, level=0)

async def main():
    """ESP32 BLE + RTC + Deep Sleep 메인 프로세스"""

    # 🔄 RTC 관리 모듈 초기화
    rtc_manager = RTCManager()
    ble_manager = BLEManager(rtc_manager)
    sensor_logger = SensorLogger()

    # ✅ RTC 데이터 손실 또는 등록이 안 된 경우, BLE 등록 광고 실행
    if ble_manager._registered_mac is None or rtc_manager.latest_time is None or rtc_manager.period is None:
        print("⚠️ BLE 등록 필요 또는 RTC 데이터 손실 감지! 등록을 다시 진행합니다.")
        await ble_manager.advertise()  # 등록이 끝날 때까지 광고

        # 센서 로그
        current_time = rtc_manager.format_rtc_datetime();
        sensor_logger.get_sensor_data(current_time)

        rtc_manager.enter_deep_sleep()  # 등록 후 다시 deep sleep 진입

    # ✅ 최신 wake-up 시간이 되었는지 확인
    if rtc_manager.check_wake_time():
        print("🔔 Time to wake up, resuming operation...")

        # 1. 센서 데이터 기록
        current_time = rtc_manager.format_rtc_datetime();
        sensor_logger.get_sensor_data(current_time)

        # 2. BLE 기기 스캔 후 데이터 전송 (생략 가능)

        # 3. 최신 시간을 업데이트 후 RTC 메모리에 저장
        latest_time = rtc_manager.latest_time + rtc_manager.period
        rtc_manager.save_rtc_memory(latest_time,rtc_manager.period)

        # 4. 다음 wake up 시간만큼 다시 deep sleep 모드로 진입
        rtc_manager.enter_deep_sleep()
    else:
        print("⏳ Not time to wake up yet. advertising for connection...")
        # 깨어날 시간이 아닌데 깨어난 경우
        # 1분 동안 advertise를 켜놓고 새로 들어오는 설정 및 데이터 요청에 대응
        await ble_manager.advertise_for_wakeup(timeout=60000) 

        if not ble_manager.connected_device:  # 광고 후에도 연결이 없으면 Deep Sleep
            print("⏳ No connection detected. Entering Deep Sleep.")
            rtc_manager.enter_deep_sleep()
        
# boot하면 main 실행
asyncio.run(main())
