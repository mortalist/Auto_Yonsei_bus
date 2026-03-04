# 🚌 연세대 셔틀버스 자동 예약봇

> 매일 아침 버스 예약하는 거 너무 귀찮지 않음? 그래서 만듦 ㅇㅇ

---

## ✨ 뭐하는 코드임?

연세대 포털에서 **국제캠퍼스 ↔ 신촌캠퍼스 셔틀버스**를 자동으로 예약해주는 스크립트.
Playwright로 브라우저 직접 조작하는 방식이라 웬만하면 잘 됨.

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

> 버스 칸 꽉 차기 전에 실행하세요 🏃
