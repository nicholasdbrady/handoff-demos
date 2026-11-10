"""Verify the fal slide against its local capture manifest in Microsoft Edge."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:3080")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=5)
    args = parser.parse_args()

    manifest_path = Path(__file__).parent.joinpath(
        "public", "demos", "fal-video", "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_evidence = json.loads(
        manifest_path.with_name("evidence.json").read_text(encoding="utf-8")
    )
    submitted_prompts = {
        result["model"]: result["request"]["prompt"]
        for result in source_evidence["measured_generation_results"]
    }
    assets = [
        asset for asset in manifest["assets"]
        if asset["kind"] == "video" and ".mp4" in asset["path"].lower()
    ]
    assert len(assets) == args.expected_count, (
        f"Expected {args.expected_count} video assets, found {len(assets)}"
    )
    assert all(asset.get("prompt") and asset.get("poster") for asset in assets), (
        "Each video must have its exact prompt and a poster."
    )
    for asset in assets:
        assert asset["prompt"] == submitted_prompts.get(asset["model"]), (
            f"Prompt does not match the recorded request for {asset['model']}."
        )
    if len(assets) > 1:
        assert all(asset.get("model_name") and asset.get("label") for asset in assets), (
            "Each video needs a model selector name and display label."
        )
        assert len({asset["model_name"] for asset in assets}) == len(assets), (
            "Model selector names must be distinct."
        )

    args.output.mkdir(parents=True, exist_ok=True)
    evidence = []
    responses: dict[str, list[dict[str, object]]] = {}
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        context.add_init_script(
            """if (window === window.top) localStorage.setItem('slidev-sync-directions',
              JSON.stringify({viewerSend:false, viewerReceive:false,
                presenterSend:false, presenterReceive:false}))"""
        )
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))

        def record_response(response) -> None:
            path = urlsplit(response.url).path
            if path.lower().endswith(".mp4"):
                responses.setdefault(path, []).append({
                    "status": response.status,
                    "content_type": response.headers.get("content-type"),
                })

        page.on("response", record_response)

        for width, height in [(800, 450), (1280, 720), (1920, 1080)]:
            page.set_viewport_size({"width": width, "height": height})
            for theme in ["light", "dark"]:
                page.emulate_media(color_scheme=theme, reduced_motion="reduce")
                page.goto(f"{args.url}/22", wait_until="networkidle", timeout=90_000)
                page.evaluate(
                    "(dark) => document.documentElement.classList.toggle('dark', dark)",
                    theme == "dark",
                )
                demo = page.locator('.capture-demo[aria-label="fal-video demo"]').filter(
                    visible=True
                ).first
                demo.locator("video").wait_for()
                buttons = demo.locator(".capture-models button")
                assert buttons.count() == (len(assets) if len(assets) > 1 else 0)
                assert demo.get_by_role("button", name=re.compile("Run live")).count() == 0
                assert demo.locator(".capture-metrics").count() == 0

                previous = None
                for index, asset in enumerate(assets):
                    if len(assets) > 1:
                        button = buttons.nth(index)
                        assert button.inner_text() == asset["model_name"]
                        if index:
                            button.click()
                        assert button.get_attribute("aria-pressed") == "true"
                    if previous is not None:
                        assert previous.evaluate("(video) => video.paused"), (
                            "Switching clips must pause the previous video."
                        )

                    video = demo.locator("video")
                    video.wait_for()
                    handle = video.element_handle()
                    assert handle is not None
                    page.wait_for_function(
                        "(video) => video.readyState >= 1", arg=handle, timeout=15_000
                    )
                    assert video.evaluate("(video) => video.paused"), (
                        "A selected clip must not autoplay."
                    )
                    assert demo.locator(".capture-prompt").text_content() == asset["prompt"]
                    assert video.get_attribute("aria-label") == asset["alt"]
                    assert urlsplit(urljoin(args.url, video.get_attribute("src"))).path == (
                        urlsplit(urljoin(args.url, asset["path"])).path
                    )
                    assert urlsplit(urljoin(args.url, video.get_attribute("poster"))).path == (
                        urlsplit(urljoin(args.url, asset["poster"])).path
                    )
                    poster = page.evaluate(
                        """async url => {
                          const image = new Image();
                          image.src = url;
                          await image.decode();
                          return {width: image.naturalWidth, height: image.naturalHeight};
                        }""",
                        urljoin(args.url, asset["poster"]),
                    )
                    assert poster["width"] > 0 and poster["height"] > 0
                    if len(assets) > 1:
                        assert asset["label"] in demo.locator(".capture-scene").inner_text()
                        assert demo.locator(".capture-origin").inner_text() == (
                            "Microsoft Foundry · fal · public preview"
                        )

                    geometry = demo.evaluate(
                        """root => {
                          const prompt = root.querySelector('.capture-prompt');
                          const body = root.querySelector('.capture-body');
                          const details = root.querySelector('.capture-details');
                          const media = root.querySelector('.capture-media');
                          const video = root.querySelector('video').getBoundingClientRect();
                          const toolbar = root.querySelector('.capture-toolbar').getBoundingClientRect();
                          const slide = root.closest('.slidev-layout').getBoundingClientRect();
                          const rect = prompt.getBoundingClientRect();
                          const boundary = body.getBoundingClientRect();
                          const overlap = (a, b) => a.left < b.right && a.right > b.left
                            && a.top < b.bottom && a.bottom > b.top;
                          return {
                            fontSize: parseFloat(getComputedStyle(prompt).fontSize),
                            detailsOverflow: details.scrollHeight > details.clientHeight + 1
                              || details.scrollWidth > details.clientWidth + 1,
                            mediaOverflow: media.scrollHeight > media.clientHeight + 1
                              || media.scrollWidth > media.clientWidth + 1,
                            promptOverlapsVideo: overlap(rect, video),
                            promptOverlapsToolbar: overlap(rect, toolbar),
                            promptFits: rect.top >= slide.top - 2
                              && rect.bottom <= Math.min(slide.bottom, boundary.bottom) + 2
                              && rect.left >= slide.left - 2
                              && rect.right <= slide.right + 2
                          };
                        }"""
                    )
                    assert geometry["fontSize"] >= 24, geometry
                    assert not geometry["detailsOverflow"], geometry
                    assert not geometry["mediaOverflow"], geometry
                    assert not geometry["promptOverlapsVideo"], geometry
                    assert not geometry["promptOverlapsToolbar"], geometry
                    assert geometry["promptFits"], geometry

                    screenshot = args.output.joinpath(
                        f"fal-{index + 1:02d}-{theme}-{width}.png"
                    )
                    page.screenshot(path=str(screenshot))
                    row = {
                        "asset": asset["path"],
                        "theme": theme,
                        "width": width,
                        "prompt_matches": True,
                        "poster_matches": True,
                        "poster_dimensions": poster,
                        "geometry": geometry,
                        "screenshot": str(screenshot),
                    }
                    if width == 1280 and theme == "light":
                        handle.evaluate(
                            "async video => { video.muted = true; await video.play(); }"
                        )
                        page.wait_for_function(
                            "(video) => !video.paused && video.currentTime > 0.25",
                            arg=handle,
                            timeout=15_000,
                        )
                        row["playback"] = handle.evaluate(
                            """video => ({readyState: video.readyState,
                              currentTime: video.currentTime, duration: video.duration,
                              width: video.videoWidth, height: video.videoHeight})"""
                        )
                    evidence.append(row)
                    previous = handle

                if width == 1280 and theme == "light":
                    page.keyboard.press("ArrowRight")
                    page.wait_for_url("**/23", timeout=5_000)
                    assert previous is not None
                    page.wait_for_function(
                        "(video) => video.paused", arg=previous, timeout=2_000
                    )

        if len(assets) > 1:
            page.goto(f"{args.url}/22", wait_until="networkidle", timeout=90_000)
            buttons = page.locator(".capture-models button").filter(visible=True)
            buttons.nth(1).focus()
            page.keyboard.press("Space")
            assert buttons.nth(1).evaluate("(button) => document.activeElement === button")
            assert buttons.nth(1).get_attribute("aria-pressed") == "true"
            page.keyboard.press("Shift+Tab")
            assert buttons.nth(0).evaluate("(button) => document.activeElement === button")
            page.keyboard.press("Enter")
            assert buttons.nth(0).get_attribute("aria-pressed") == "true"
            assert buttons.nth(0).evaluate("(button) => document.activeElement === button")

        page.route("**/demo-api/health", lambda route: route.abort())
        page.goto(f"{args.url}/22", wait_until="networkidle", timeout=90_000)
        demo = page.locator('.capture-demo[aria-label="fal-video demo"]').filter(
            visible=True
        ).first
        demo.locator("video").wait_for()
        assert demo.locator(".capture-live").count() == 0, (
            "Captured clips must work without the live adapter."
        )

        browser.close()

    for asset in assets:
        path = urlsplit(urljoin(args.url, asset["path"])).path
        assert any(
            item["status"] in (200, 206)
            and str(item["content_type"]).startswith("video/mp4")
            for item in responses.get(path, [])
        ), f"No successful video response recorded for {path}"
    assert not errors, "\n".join(errors)
    args.output.joinpath("fal-clips-evidence.json").write_text(
        json.dumps({"assets": len(assets), "evidence": evidence, "responses": responses}, indent=2),
        encoding="utf-8",
    )
    checks = "exact prompts, posters, playback, navigation, and geometry"
    if len(assets) > 1:
        checks += ", plus selector and keyboard focus"
    print(f"Edge: {len(assets)} clip(s), {len(evidence)} captures; {checks} verified.")


if __name__ == "__main__":
    main()
