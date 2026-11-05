"""Capture Edge slides; inference requires an explicit --live-slide argument."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main() -> None:
    """Inspect rendered content before interaction, then capture both themes."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url", default="http://127.0.0.1:3070")
    parser.add_argument("--live-slide", type=int)
    parser.add_argument("--lane", help="Accessible name of one lane's Run button")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--chat-review", action="store_true")
    parser.add_argument("--thinking-capture", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": args.width, "height": args.height}, device_scale_factor=1)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        requests = []
        responses = []

        def capture_response(response) -> None:
            if "/demo-api/stream/" in response.url or "/fusion-api/run" in response.url:
                responses.append(response)

        page.on("response", capture_response)
        for slide in ([args.live_slide] if args.live_slide else [12, 15, 16, 19] if args.chat_review else [3, 6, 7, 12, 15, 16, 19]):
            page.emulate_media(color_scheme="light")
            page.goto(f"{args.url}/{slide}", wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_load_state("networkidle", timeout=90_000)
            page.locator(".slidev-page").filter(visible=True).first.wait_for()
            if args.live_slide:
                button = args.lane or ("Invoke prepared agent · live" if slide in (6, 7)
                                       else "Send to both")
                with page.expect_response(lambda response: "/demo-api/stream/" in response.url or "/fusion-api/run" in response.url, timeout=30_000):
                    page.get_by_role("button", name=button, exact=True).click()
                if args.thinking_capture:
                    page.wait_for_timeout(7000)
                    window = page.locator('.chat-window[aria-busy=true]').first
                    window.wait_for()
                    details = window.locator(".chat-thinking")
                    for theme in ("light", "dark"):
                        page.evaluate("(dark) => document.documentElement.classList.toggle('dark', dark)", theme == "dark")
                        page.wait_for_timeout(250)
                        details.evaluate("(node) => node.open = false")
                        page.screenshot(path=str(args.output / f"slide-{slide:02d}-{theme}-thinking-collapsed.png"))
                        details.locator("summary").click()
                        page.screenshot(path=str(args.output / f"slide-{slide:02d}-{theme}-thinking-expanded.png"))
                    (args.output / f"slide-{slide:02d}-thinking-evidence.json").write_text(
                        json.dumps({"live_triggered": True, "text": window.inner_text(),
                                    "recorded": window.locator(".chat-recorded").count() > 0}, indent=2), encoding="utf-8")
                page.wait_for_function(
                    "() => !document.querySelector('.chat-window[aria-busy=true]') && ![...document.querySelectorAll('button')].some(b => /Sending in series|Invoking\\.\\.\\./.test(b.textContent))",
                    timeout=590_000,
                )
                requests = [{"url": response.url, "status": response.status, "body": response.text()}
                            for response in responses]
            elif slide in (12, 15, 16):
                page.get_by_role("combobox").select_option("recorded")
                page.get_by_role("button", name="Send to both", exact=True).click()
                expect(page.locator(".chat-state:visible")).to_have_text(["Done", "Done"])
                badges = page.locator(".chat-recorded:visible")
                expect(badges).to_have_text(["SYNTHETIC", "SYNTHETIC"])
            elif slide == 19:
                page.get_by_text("Not included in this portable export", exact=True).wait_for()
            for theme in ["light", "dark"]:
                page.emulate_media(color_scheme=theme)
                page.evaluate("(dark) => document.documentElement.classList.toggle('dark', dark)", theme == "dark")
                page.wait_for_timeout(300)
                page.screenshot(path=str(args.output / f"slide-{slide:02d}-{theme}.png"))
                layout = page.evaluate("""() => [...document.querySelectorAll('.chat-window')].map(window => {
                  const rectangle = window.getBoundingClientRect();
                  const composer = window.querySelector('.chat-composer').getBoundingClientRect();
                  const transcript = window.querySelector('[role=log]');
                  const style = getComputedStyle(window);
                  return {title: window.getAttribute('aria-label'), width: rectangle.width, height: rectangle.height,
                    composer_inside: composer.bottom <= rectangle.bottom + 1,
                    horizontal_overflow: window.scrollWidth > window.clientWidth + 1,
                    log_live: transcript?.getAttribute('aria-live'), foreground: style.color, background: style.backgroundColor,
                    body_font: getComputedStyle(window.querySelector('.chat-user-message p') ?? window).fontSize,
                    metadata_font: getComputedStyle(window.querySelector('.chat-metrics')).fontSize}
                })""")
                if layout:
                    assert all(row["composer_inside"] and not row["horizontal_overflow"] for row in layout), layout
                    assert all(float(row["body_font"][:-2]) >= 16 and float(row["metadata_font"][:-2]) >= 13 for row in layout), layout
                (args.output / f"slide-{slide:02d}-{theme}-evidence.json").write_text(
                    json.dumps({"live_triggered": bool(args.live_slide), "text": page.locator("body").inner_text(),
                                "requests": requests, "layout": layout, "page_errors": errors}, indent=2), encoding="utf-8")
                if args.chat_review:
                    page.set_viewport_size({"width": 800, "height": 720})
                    page.screenshot(path=str(args.output / f"slide-{slide:02d}-{theme}-narrow.png"))
                    page.set_viewport_size({"width": args.width, "height": args.height})
        browser.close()
    known_prefix = "Failed to patch FloatingVue TypeError: Cannot read properties of undefined (reading 'Popper')"
    unexpected = [error for error in errors if not error.startswith(known_prefix)]
    if errors:
        print(f"Observed {len(errors) - len(unexpected)} known upstream FloatingVue console errors; preserved in evidence JSON.")
    if unexpected:
        raise AssertionError("Unexpected browser errors observed: " + "\n".join(unexpected))
    print(f"Edge captures saved to {args.output}")


if __name__ == "__main__":
    main()
