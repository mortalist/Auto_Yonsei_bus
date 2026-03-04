from playwright.sync_api import sync_playwright
import time
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


# ──────────────────────────────────────────────
# 설정값 — 여기만 바꾸면 됩니다
# ──────────────────────────────────────────────
LOGIN_ID       = "2023199110"
LOGIN_PW       = "Mortalist02!"

DEPARTURE      = "신촌캠퍼스"   # 출발지역
RIDE_REASON    = "수업"         # 탑승 사유
TARGET_DATE    = "20260305"     # 예약일자 (YYYYMMDD)
TARGET_TIME    = "07:20 ~"      # 예약할 시간대
# ──────────────────────────────────────────────

TOTAL_STEPS = 6


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def step_ok(n, msg):
    console.print(f"  [dim][{n}/{TOTAL_STEPS}][/dim] [bold green]✓[/bold green]  {msg}  [dim]{_ts()}[/dim]")


def step_fail(n, msg):
    console.print(f"  [dim][{n}/{TOTAL_STEPS}][/dim] [bold red]✗[/bold red]  [red]{msg}[/red]  [dim]{_ts()}[/dim]")


def fill_combobox(page, name, value):
    combo = page.get_by_role("combobox", name=name)
    combo.click()
    combo.press("Control+a")
    combo.press("Backspace")
    combo.type(value, delay=100)


def fill_datebox(page, name, value):
    textbox = page.get_by_role("textbox", name=name)
    textbox.click()
    textbox.press("Control+a")
    textbox.press("Backspace")
    for ch in value:
        textbox.press(ch, delay=100)
    textbox.press("Enter")


def accept_dialog(dialog):
    dialog.accept()


def run():
    # ── 헤더 출력 ────────────────────────────────────────────
    console.print()
    console.print(Panel(
        "[bold blue]연세대학교 셔틀버스 자동 예약 시스템[/bold blue]",
        border_style="blue",
        expand=False,
        padding=(0, 6),
    ))

    date_fmt = f"{TARGET_DATE[:4]}-{TARGET_DATE[4:6]}-{TARGET_DATE[6:]}"
    info = Table(box=box.ROUNDED, show_header=False, border_style="dim", padding=(0, 1))
    info.add_column(style="dim")
    info.add_column(style="bold white")
    info.add_row("출발지역", DEPARTURE)
    info.add_row("예약일자", date_fmt)
    info.add_row("예약시간", TARGET_TIME)
    info.add_row("탑승사유", RIDE_REASON)
    console.print(Panel(info, title="[dim]예약 정보[/dim]", border_style="dim", expand=False))
    console.print()

    # ── 자동화 시작 ──────────────────────────────────────────
    try:
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

            # ── 1. 포털 접속 및 로그인 ──────────────────────
            with console.status(f"  [dim][1/{TOTAL_STEPS}][/dim]  포털 접속 및 로그인 중..."):
                page.goto("https://portal.yonsei.ac.kr")
                page.wait_for_load_state("networkidle")
                page.get_by_role("link", name="로그인").first.click()
                page.wait_for_load_state("networkidle")
                page.locator("#loginId").fill(LOGIN_ID)
                page.locator("input[type='password']").first.fill(LOGIN_PW)
                page.get_by_role("link", name="로그인(Login)").click()
                page.wait_for_load_state("networkidle")
                print("로그인 시도 완료, 로그인 상태 확인 중...")
                time.sleep(3)
            step_ok(1, "포털 접속 및 로그인 완료")

            # ── 2. 국제캠퍼스 셔틀버스 탭 열기 ─────────────
            with console.status(f"  [dim][2/{TOTAL_STEPS}][/dim]  셔틀버스 페이지 이동 중..."):
                bus_page = None
                for frame in page.frames:
                    try:
                        link = frame.locator("a", has_text="국제캠퍼스").first
                        link.wait_for(state="attached", timeout=2000)
                        with context.expect_page() as new_page_info:
                            link.click()
                        bus_page = new_page_info.value
                        bus_page.wait_for_load_state("networkidle")
                        break
                    except Exception:
                        continue

            if bus_page is None:
                step_fail(2, "셔틀버스 링크를 찾을 수 없습니다")
                raise RuntimeError("국제캠퍼스 셔틀버스 링크를 찾을 수 없습니다.")
            step_ok(2, "셔틀버스 페이지 이동 완료")

            # ── 3. 예약 화면 진입 ───────────────────────────
            with console.status(f"  [dim][3/{TOTAL_STEPS}][/dim]  예약 화면 진입 중..."):
                time.sleep(3)
                bus_page.get_by_role("button", name="예약").click()
                bus_page.wait_for_load_state("networkidle")
            step_ok(3, "예약 화면 진입 완료")

            # ── 4. 출발지역 및 예약일자 입력 ────────────────
            with console.status(f"  [dim][4/{TOTAL_STEPS}][/dim]  출발지/날짜 입력 및 조회 중..."):
                fill_combobox(bus_page, "출발지역", DEPARTURE)
                time.sleep(10)
                fill_datebox(bus_page, "예약일자", TARGET_DATE)
                bus_page.wait_for_load_state("networkidle")
                time.sleep(10)
                try:
                    bus_page.locator("div.cl-grid-row").first.wait_for(state="attached", timeout=15000)
                except Exception:
                    step_fail(4, "시간표 그리드 로드 실패")
                    raise

            row_count = bus_page.locator("div.cl-grid-row").count()
            step_ok(4, f"출발지/날짜 입력 완료  [dim](시간표 {row_count}행 로드됨)[/dim]")

            # ── 5. 탑승 사유 선택 ───────────────────────────
            with console.status(f"  [dim][5/{TOTAL_STEPS}][/dim]  탑승 사유 선택 중..."):
                target_row = bus_page.locator("div.cl-grid-row").filter(has_text=TARGET_TIME).first
                reason_box = target_row.locator(
                    ".cl-control.cl-combobox.display-text > div > div > .cl-text"
                ).first
                reason_box.click(force=True)
                bus_page.keyboard.type(RIDE_REASON, delay=100)
                bus_page.keyboard.press("Enter")
                time.sleep(2)
            step_ok(5, f"탑승 사유 선택 완료  [dim]({RIDE_REASON})[/dim]")

            # ── 6. 신청 버튼 클릭 + 확인 팝업 수락 ─────────
            with console.status(f"  [dim][6/{TOTAL_STEPS}][/dim]  예약 신청 중..."):
                target_row = bus_page.locator("div.cl-grid-row").filter(has_text=TARGET_TIME).first
                신청_btn = target_row.locator(".cl-text", has_text="신청").first
                bus_page.evaluate("window.confirm = () => true; window.alert = () => {};")
                bus_page.on("dialog", accept_dialog)
                신청_btn.click()
                time.sleep(2)
            step_ok(6, "예약 신청 완료!")

            browser.close()

        console.print()
        console.print(Panel(
            "[bold green]  예약이 성공적으로 완료되었습니다!  [/bold green]",
            border_style="green",
            expand=False,
            padding=(0, 4),
        ))
        console.print()

    except RuntimeError as e:
        console.print()
        console.print(Panel(
            f"[bold red]오류:[/bold red] [red]{e}[/red]",
            border_style="red",
            expand=False,
            padding=(0, 2),
        ))
    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]예상치 못한 오류가 발생했습니다[/bold red]\n[red]{e}[/red]",
            border_style="red",
            expand=False,
            padding=(0, 2),
        ))


if __name__ == "__main__":
    run()
