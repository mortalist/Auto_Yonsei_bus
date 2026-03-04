from playwright.sync_api import sync_playwright
from secret import LOGIN_ID, LOGIN_PW

# ──────────────────────────────────────────────
# 설정값 — 여기만 바꾸면 됩니다
# ──────────────────────────────────────────────

DEPARTURE      = "신촌캠퍼스"   # 출발지역
RIDE_REASON    = "수업"         # 탑승 사유
TARGET_DATE    = "20260305"     # 예약일자 (YYYYMMDD)
TARGET_TIME    = "07:20 ~"  # 예약할 시간대
# ──────────────────────────────────────────────


def fill_combobox(page, name, value):
    """콤보박스를 클릭 후 기존 값 지우고 새 값 입력"""
    box = page.get_by_role("combobox", name=name)
    box.click()
    box.press("Control+a")
    box.press("Backspace")
    box.type(value, delay=100)


def fill_datebox(page, name, value):
    """날짜 텍스트박스를 클릭 후 기존 값 지우고 숫자 하나씩 입력"""
    box = page.get_by_role("textbox", name=name)
    box.click()
    box.press("Control+a")
    box.press("Backspace")
    for ch in value:
        box.press(ch, delay=100)
    box.press("Enter")


def accept_dialog(dialog):
    """신청 확인 팝업을 자동으로 수락"""
    print(f"[확인창] {dialog.message}")
    dialog.accept()


def run():
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
        page.set_default_timeout(10000)

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
        page.screenshot(path="debug_after_login.png")
        print(f"[DEBUG] 로그인 후 URL: {page.url}")
        print(f"[DEBUG] 전체 frame 수: {len(page.frames)}")
        for i, frame in enumerate(page.frames):
            print(f"[DEBUG] Frame {i}: {frame.url}")

        # ── 2. 국제캠퍼스 셔틀버스 탭 열기 ─────────
        # 포털 내부 iframe을 순회하며 링크를 찾습니다.
        # 링크 클릭 시 새 탭이 열리므로 expect_page()로 캡처합니다.
        bus_page = None
        for frame in page.frames:
            try:
                # 부분 텍스트 매칭으로 더 유연하게 탐색
                link = frame.locator("a", has_text="국제캠퍼스").first
                link.wait_for(state="attached", timeout=2000)
                with context.expect_page() as new_page_info:
                    link.click()
                bus_page = new_page_info.value
                bus_page.get_by_role("button", name="예약").wait_for(state="visible")
                break
            except Exception:
                continue

        if bus_page is None:
            page.screenshot(path="debug_link_not_found.png")
            print("[DEBUG] 링크를 찾지 못했습니다. debug_link_not_found.png 를 확인하세요.")
            raise RuntimeError("국제캠퍼스 셔틀버스 링크를 찾을 수 없습니다.")

        # ── 3. 예약 화면 진입 ───────────────────────
        bus_page.get_by_role("button", name="예약").click()
        bus_page.get_by_role("combobox", name="출발지역").wait_for(state="visible")

        # ── 4. 출발지역 및 예약일자 입력 ───────────
        fill_combobox(bus_page, "출발지역", DEPARTURE)
        bus_page.get_by_role("textbox", name="예약일자").wait_for(state="visible")
        fill_datebox(bus_page, "예약일자", TARGET_DATE)

        # 그리드가 실제로 렌더링될 때까지 대기 (최대 15초)
        # cl-viewing 클래스로 인해 DOM엔 있지만 CSS상 hidden이므로 attached로 확인
        try:
            bus_page.locator("div.cl-grid-row").first.wait_for(state="attached", timeout=15000)
        except Exception:
            bus_page.screenshot(path="debug_grid_not_loaded.png")
            print("[DEBUG] 그리드가 로드되지 않았습니다. debug_grid_not_loaded.png 확인하세요.")
            raise

        bus_page.screenshot(path="debug_grid_loaded.png")
        print(f"[DEBUG] 그리드 row 수: {bus_page.locator('div.cl-grid-row').count()}")

        # ── 5. 탑승 사유 선택 ───────────────────────
        # 해당 시간대 행을 찾아 탑승 사유 콤보박스를 클릭합니다.
        bus_page.locator("div.cl-grid-row").filter(has_text=TARGET_TIME).first.wait_for(state="attached")
        target_row = bus_page.locator("div.cl-grid-row").filter(has_text=TARGET_TIME).first
        reason_box = target_row.locator(".cl-control.cl-combobox.display-text > div > div > .cl-text").first
        reason_box.click(force=True)
        bus_page.keyboard.type(RIDE_REASON, delay=100)
        bus_page.keyboard.press("Enter")

        신청_btn = target_row.locator(".cl-text", has_text="신청").first
        신청_btn.wait_for(state="visible")
        bus_page.screenshot(path="debug_after_reason_selected.png")

        # ── 6. 신청 버튼 클릭 + 확인 팝업 수락 ─────
        # 신청 클릭 → "신청하시겠습니까?" → "신청되었습니다" 순서로
        # 팝업이 두 번 뜨므로 on()으로 등록해 모두 자동 수락합니다.
        # 주 처리: JS로 confirm/alert를 직접 덮어씁니다.
        #   confirm() → true  (확인 클릭과 동일)
        #   alert()   → 즉시 닫힘
        # failsafe: JS 덮어쓰기가 통하지 않을 경우를 대비해 Playwright 핸들러도 등록합니다.
        bus_page.evaluate("window.confirm = () => true; window.alert = () => {};")
        bus_page.on("dialog", accept_dialog)
        신청_btn.click()

        print("탑승 신청 완료!")
        input("엔터를 누르면 브라우저가 닫힙니다...")
        browser.close()


if __name__ == "__main__":
    run()
