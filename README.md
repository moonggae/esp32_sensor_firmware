# ESP32 BLE Sensor Logger

## 개요
ESP32 기반 BLE 센서 로거로, 온습도 데이터를 측정하고 BLE를 통해 전송하며, 일정 주기마다 Deep Sleep 모드로 진입하는 시스템입니다.

## 프로젝트 구조
| 디렉토리/파일 | 설명 |
|--------------|--------------------------------------------------|
| `lib\` | 라이브러리 폴더 (aioble, bme280) |
| `boot.py` | 시스템 초기화 및 메인 실행 흐름 관리 |
| `rtc_manager.py` | RTC(Real-Time Clock) 관리 및 Deep Sleep 스케줄링 |
| `aioble_manager.py` | BLE 통신 및 GATT 서비스 관리 |
| `sensor_logger.py` | BME280 센서 데이터 측정 및 CSV 파일 저장 |
| `file_utils.py` | 파일 입출력 관련 유틸리티 함수 제공 |

## 주요 기능
| 기능 | 설명 |
|------|--------------------------------------------------|
| BLE 등록 및 통신 | BLE를 통해 기기 등록 및 데이터 송수신 수행 |
| RTC 관리 | 시간 설정 및 Wake-up 시간 계산 |
| 센서 데이터 측정 | BME280 센서에서 온도 및 습도 데이터 측정 |
| 데이터 저장 | 측정된 데이터를 CSV 파일에 저장 및 관리 |
| Deep Sleep | 주기적으로 절전 모드에 진입 후 자동 Wake-up |

## 실행 흐름
1. **ESP32 부팅 시** `boot.py` 실행
2. `RTCManager` 및 `BLEManager` 초기화
3. 기기 등록이 완료될 때까지 BLE 광고 수행
4. 등록 후 RTC 시간 동기화 및 센서 데이터 측정
5. 측정된 데이터 BLE를 통해 전송
6. 지정된 주기 후 Deep Sleep 모드 진입
7. Wake-up 후 다시 센서 데이터 측정

## 설치 및 실행
1. ESP32에 Micropython 펌웨어 설치
2. 프로젝트 파일 업로드
3. ESP32 재부팅 후 BLE 연결 및 데이터 송수신 테스트

## 참고
- `machine.deepsleep`를 활용한 저전력 모드 구현
- `aioble` 라이브러리를 사용하여 BLE GATT 서비스 구현
- `machine.RTC`를 활용하여 Deep Sleep 후 시간 유지
- `uos`를 활용한 CSV 데이터 관리

## License
This project includes code from the Adafruit BME280 Python library and is licensed under the MIT License.

See the [LICENSE](./LICENSE) file for details.
