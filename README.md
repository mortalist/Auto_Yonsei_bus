# 🚌 연세대 셔틀버스 자동 예약봇

> 연세대 포털에서 국제캠퍼스 ↔ 신촌캠퍼스 셔틀버스를 자동으로 예약해주는 스크립트입니다.
> Playwright로 브라우저를 직접 제어하는 방식이라, 대부분의 경우 안정적으로 동작합니다.

---

## 🛠 사용 스택

- Python 3
- [Playwright](https://playwright.dev/python/) (브라우저 자동화)

---

## 🚀 사용법

### 1. 의존성 설치

```bash
pip install playwright
playwright install chromium
```

### 2. 자격증명 설정

`secret.example.py`를 복사해서 `secret.py` 만들고 본인 정보 입력

```bash
cp secret.example.py secret.py
```

```python
# secret.py
LOGIN_ID = "학번"
LOGIN_PW = "포털 비밀번호"
```

### 3. 예약 설정

`main.py` 상단 설정값 수정

```python
DEPARTURE   = "신촌캠퍼스"   # 출발지역
RIDE_REASON = "수업"          # 탑승 사유
TARGET_DATE = "20260305"      # 예약일자 (YYYYMMDD)
TARGET_TIME = "07:20 ~"       # 예약할 시간대
```

### 4. 실행

```bash
python main.py
```

---

## ⚠️ 주의사항

- `secret.py`는 절대 커밋하지 말 것 (`.gitignore`에 이미 추가됨)
- 포털 구조 바뀌면 locator 수정 필요할 수도 있음
- 본인 계정으로만 쓸 것

---

## 📁 프로젝트 구조

```
auto_yonsei_bus/
├── main.py               # 메인 스크립트
├── secret.py             # 🔒 자격증명 (git 제외)
├── secret.example.py     # 자격증명 예시
└── .gitignore
```

---

## 💡 추천 사용법 (서버 자동 실행)

이론적으로 가장 편한 방법은 **버스 예약일 2일 전 오후 2시** (예매 오픈 시간)에 자동으로 실행되도록 서버에 crontab 등으로 등록해두는 것.

### crontab 예시 (Linux/macOS 서버)

```bash
# crontab -e 로 편집
# 오후 1시 57분에 실행 — 포털 접속 후 WAITFOR_TWO 기능이 서버 시각 기준 14:00:00을 기다렸다가 예약
57 13 * * * /usr/bin/python3 /path/to/auto_yonsei_bus/main.py >> /path/to/auto_yonsei_bus/log.txt 2>&1
```

> `WAITFOR_TWO = True`로 설정하면 스크립트가 포털에 미리 접속해 두고, 포털 서버 시각이 정확히 14:00:00이 되는 순간 예약을 시도합니다. 로컬 시간 오차와 무관하게 서버 시간 기준으로 동작합니다.

### 흐름 요약

1. 예약하고 싶은 날짜 **2일 전** = 예매 오픈일
2. 오픈일 **오후 1시 57분** → crontab이 스크립트 실행, 포털 접속 완료
3. **오후 2시 정각** → 서버 시간 확인 후 즉시 예약 시도 → 예약 완료

> 🗒️ `TARGET_DATE`를 실행 시점 기준으로 자동 계산하도록 `main.py`를 수정해두면 crontab에 한 번만 등록해도 계속 쓸 수 있음.

---

> 버스 칸 꽉 차기 전에 실행하세요 🏃

