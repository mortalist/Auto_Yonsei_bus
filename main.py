import time
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from playwright.sync_api import sync_playwright
from secret import LOGIN_ID, LOGIN_PW

# ──────────────────────────────────────────────
# 설정값 — 여기만 바꾸면 됩니다
# ──────────────────────────────────────────────

DEPARTURE      = "국제캠퍼스"   # 출발지역
RIDE_REASON    = "수업"         # 탑승 사유
TARGET_DATE    = (datetime.now() + timedelta(days=2)).strftime("%Y%m%d")  # 예약일자 (오늘 + 2일)
TARGET_TIME    = "12:30 ~"  # 예약할 시간대
WAITFOR_TWO    = True           
# ──────────────────────────────────────────────


def fill_combobox(page, name, value):
    """콤보박스를 클릭 후 기존 값 지우고 새 값 입력"""
    box = page.get_by_role("combobox", name=name)
    box.click()
    box.press("Control+a")
    box.press("Backspace")
    box.type(value, delay=1)


def fill_datebox(page, name, value):
    """날짜 텍스트박스를 클릭 후 기존 값 지우고 숫자 하나씩 입력"""
    box = page.get_by_role("textbox", name=name)
    box.click()
    box.press("Control+a")
    box.press("Backspace")
    for ch in value:
        box.press(ch, delay=1)
    box.press("Enter")


def run():
    did_alert = [False]

    def accept_dialog(dialog):
        print(f"[확인창] {dialog.message}")
        did_alert[0] = True
        dialog.accept()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page.set_default_timeout(200000)

        # ── 1. 포털 접속 및 로그인 ──────────────────
        page.goto("https://portal.yonsei.ac.kr")
        page.wait_for_load_state("networkidle")

        page.get_by_role("link", name="로그인").first.wait_for(state="visible")

        page.get_by_role("link", name="로그인").first.click()
        page.locator("#loginId").wait_for(state="visible")

        page.locator("#loginId").fill(LOGIN_ID)
        page.locator("input[type='password']").first.fill(LOGIN_PW)
        page.get_by_role("link", name="로그인(Login)").click()
        page.locator("iframe").first.wait_for(state="attached")  # iframe 내부 콘텐츠 로드 대기

        # 로그인 후 화면 저장 (디버그용)
        # page.screenshot(path="debug_after_login.png")
        print(f"[DEBUG] 로그인 후 URL: {page.url}")
        print(f"[DEBUG] 전체 frame 수: {len(page.frames)}")
        for i, frame in enumerate(page.frames):
            print(f"[DEBUG] Frame {i}: {frame.url}")

        # 로그인 후 선택적으로 뜨는 팝업 닫기
        닫기_btn = page.locator(".cl-text", has_text="닫기")
        try:
            닫기_btn.wait_for(state="visible", timeout=3000)
            닫기_btn.click()
        except Exception:
            pass

        if WAITFOR_TWO:
            TARGET_HOUR = 14  # 오후 2시

            def get_server_kst():
                req = urllib.request.Request("https://portal.yonsei.ac.kr")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    date_header = resp.headers.get("Date")
                utc = parsedate_to_datetime(date_header)
                return utc.astimezone(timezone(timedelta(hours=9)))

            print("[대기] portal.yonsei.ac.kr 서버 시간 기준 14:00:00 대기 중...")
            while True:
                server_kst = get_server_kst()
                if server_kst.hour >= TARGET_HOUR:
                    print(f"[대기 완료] 서버 시각: {server_kst.strftime('%H:%M:%S')}")
                    break
                target_dt = server_kst.replace(hour=TARGET_HOUR, minute=0, second=0, microsecond=0)
                seconds_left = (target_dt - server_kst).total_seconds()
                if seconds_left > 10:
                    sleep_secs = min(seconds_left - 5, 30)
                    print(f"[대기] 잔여 {seconds_left:.1f}초 → {sleep_secs:.1f}초 후 재확인")
                    time.sleep(sleep_secs)
                else:
                    time.sleep(0.1)  # 10초 이하: 0.1초 단위 폴링


        # ── 2. 국제캠퍼스 셔틀버스 탭 열기 ─────────
        # main.jsp iframe을 URL로 직접 locate합니다.
        # 링크 클릭 시 새 탭이 열리므로 expect_page()로 캡처합니다.
        main_frame = page.frame(url="**/ui/thirdparty/portal/main.jsp")
        if main_frame is None:
            raise RuntimeError("포털 메인 iframe을 찾을 수 없습니다.")

        link = main_frame.locator("a", has_text="국제캠퍼스").first
        with context.expect_page() as new_page_info:
            link.click()
        bus_page = new_page_info.value
        bus_page.get_by_role("button", name="예약").wait_for(state="visible")

        if bus_page is None:
            # page.screenshot(path="debug_link_not_found.png")
            print("[DEBUG] 링크를 찾지 못했습니다. debug_link_not_found.png 를 확인하세요.")
            raise RuntimeError("국제캠퍼스 셔틀버스 링크를 찾을 수 없습니다.")

        # dialog 핸들러는 루프 밖에서 한 번만 등록
        # (window.alert 오버라이드를 하지 않아야 Playwright가 alert를 감지할 수 있음)
        bus_page.evaluate("window.confirm = () => true;")
        bus_page.on("dialog", accept_dialog)

        attempt = 0
        while not did_alert[0] and attempt < 3:
            attempt += 1
            print(f"[시도 {attempt}/3]")
            did_alert[0] = False

            try:
                # 재시도 시 페이지 새로고침 후 예약 버튼 재진입
                if attempt > 1:
                    bus_page.reload()
                    bus_page.get_by_role("button", name="예약").wait_for(state="visible")

                # ── 3. 예약 화면 진입 ───────────────────────
                bus_page.wait_for_load_state("networkidle")
                bus_page.get_by_role("button", name="예약").click()
                bus_page.get_by_role("combobox", name="출발지역").wait_for(state="visible")

                # ── 4. 출발지역 및 예약일자 입력 ───────────
                fill_combobox(bus_page, "출발지역", DEPARTURE)
                bus_page.get_by_role("textbox", name="예약일자").wait_for(state="visible")
                fill_datebox(bus_page, "예약일자", TARGET_DATE)

                # 그리드가 실제로 렌더링될 때까지 대기 (최대 15초)
                try:
                    bus_page.locator("div.cl-grid-row").first.wait_for(state="attached", timeout=15000)
                except Exception:
                    # bus_page.screenshot(path="debug_grid_not_loaded.png")
                    print("[DEBUG] 그리드가 로드되지 않았습니다. debug_grid_not_loaded.png 확인하세요.")
                    raise

                # bus_page.screenshot(path="debug_grid_loaded.png")
                print(f"[DEBUG] 그리드 row 수: {bus_page.locator('div.cl-grid-row').count()}")

                # ── 5. 탑승 사유 선택 ───────────────────────
                bus_page.locator("div.cl-grid-row").filter(has_text=TARGET_TIME).first.wait_for(state="attached")
                target_row = bus_page.locator("div.cl-grid-row").filter(has_text=TARGET_TIME).first
                reason_box = target_row.locator(".cl-control.cl-combobox.display-text > div > div > .cl-text").first
                reason_box.click(force=True)
                bus_page.keyboard.type(RIDE_REASON, delay=100)
                bus_page.keyboard.press("Enter")
                time.sleep(1)

                신청_btn = target_row.locator(".cl-text", has_text="신청").first
                신청_btn.wait_for(state="visible")
                bus_page.screenshot(path="debug_after_reason_selected.png")

                # ── 6. 신청 버튼 클릭 + 확인 팝업 수락 ─────
                신청_btn.click(click_count=3)
                time.sleep(2)
                # bus_page.screenshot(path="debug_after_application.png")

            except Exception as e:
                print(f"[{attempt}번째 시도 실패] {e}")
                if attempt >= 3:
                    raise

        if did_alert[0]:
            print("탑승 신청 완료!")
        else:
            print("[경고] 3번 시도했으나 alert가 확인되지 않았습니다. 예약 결과를 직접 확인하세요.")

        browser.close()


if __name__ == "__main__":
    run()
