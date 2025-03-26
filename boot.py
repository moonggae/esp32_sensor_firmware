# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)

import uasyncio as asyncio
import machine
import network
from rtc_manager import RTCManager
from aioble_manager import BLEManager
from sensor_logger import SensorLogger

def battery_saver():
    # Wi-Fi 비활성화
    network.WLAN(network.STA_IF).active(False)
    # CPU 주파수 낮추기 (80 MHz) 
    machine.freq(80000000)

async def main():
    """ESP32 BLE + RTC + Deep Sleep 메인 프로세스"""
    rtc_manager = RTCManager()
    ble_manager = BLEManager(rtc_manager)
    sensor_logger = SensorLogger()
    
    # ✅ RTC 데이터 손실 또는 등록이 안 된 경우, BLE 등록 광고 실행
    if rtc_manager.latest_time is None or rtc_manager.period is None:
        print("⚠️ RTC 설정값이 없습니다. 초기 등록을 시작합니다.")
        await ble_manager.advertise_for_setting()

        current_time = rtc_manager.format_rtc_datetime()
        sensor_logger.get_sensor_data(current_time)
        rtc_manager.enter_deep_sleep()
        return 
    
    sensor_time = rtc_manager.is_sensor_time()
    advertise_time = rtc_manager.is_advertise_time()

    if sensor_time:
        print("🔔 측정 시간입니다. 센서 데이터를 수집합니다.")
        current_time = rtc_manager.format_rtc_datetime()
        sensor_logger.get_sensor_data(current_time)

        # RTC 메모리 업데이트
        latest_time = rtc_manager.latest_time + rtc_manager.period
        rtc_manager.save_rtc_memory(latest_time, rtc_manager.period)

    if advertise_time:
        print("📡 광고 시간입니다. BLE를 통해 데이터 전송 대기 중...")
        await ble_manager.advertise_for_wakeup()

    # 마지막으로 Deep Sleep 진입
    rtc_manager.enter_deep_sleep()

battery_saver()
asyncio.run(main())
