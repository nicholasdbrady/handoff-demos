"""Test a synthetic HTML fixture's isolation; never call a cloud model."""

import json

from playwright.sync_api import sync_playwright


def main() -> None:
    fixture = """<!doctype html><html><head><script src="./vendor/three.min.js"></script></head><body><p id="result">Starting</p><script>
      let isolated=false;
      try { parent.document.body.dataset.untrusted='escaped'; }
      catch { isolated=true; }
      document.getElementById('result').textContent=isolated?'Isolated script ran':'Unsafe';
    </script></body></html>"""
    manifest = {
        "slug": "kimi-k3-1-pro", "title": "Synthetic isolation test only", "status": "ready",
        "captured_at": "2026-11-09T00:00:00Z", "environment": {},
        "metrics": {"scenes": [{"requested_reasoning_effort": effort, "total_tokens": 1,
                                "reasoning_tokens": 0, "latency_ms": 1} for effort in ("none", "low", "high")]},
        "caveats": ["Test fixture, not model output"],
        "assets": [{"path": f"fixture-{effort}.txt", "kind": "text",
                    "caption": f"Unedited {effort}-effort generated HTML", "alt": "Synthetic sandbox test"}
                   for effort in ("none", "low", "high")], "live": {"supported": False},
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.add_init_script("""if (window === window.top) localStorage.setItem('slidev-sync-directions', JSON.stringify({
          viewerSend:false, viewerReceive:false, presenterSend:false, presenterReceive:false
        }))""")
        page.route("**/demos/kimi-k3-1-pro/manifest.json",
                   lambda route: route.fulfill(content_type="application/json", body=json.dumps(manifest)))
        page.route("**/demos/kimi-k3-1-pro/fixture-*.txt",
                   lambda route: route.fulfill(content_type="text/html", body=fixture))
        page.route("**/demos/kimi-k3-1-pro/vendor/three.min.js",
                   lambda route: route.fulfill(content_type="application/javascript", body="window.fixtureRuntime=true"))
        page.route("**/demos/kimi-k3-1-pro/recorded-results.json",
                   lambda route: route.fulfill(content_type="application/json", body='{"scenes":[{"question":"Synthetic test fixture only"}]}'))
        page.goto("http://127.0.0.1:3080/7", wait_until="networkidle")
        frame = page.locator("iframe.kimi-artifact")
        assert frame.get_attribute("sandbox") == "allow-scripts"
        assert frame.get_attribute("referrerpolicy") == "no-referrer"
        page.frame_locator("iframe.kimi-artifact").get_by_text("Isolated script ran", exact=True).wait_for()
        assert page.evaluate("document.body.dataset.untrusted") is None
        assert "connect-src 'none'" in frame.get_attribute("srcdoc")
        assert "form-action 'none'" in frame.get_attribute("srcdoc")
        assert page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute("content") == "frame-src 'self'; object-src 'none'"
        outbound = []
        page.route("https://example.invalid/**", lambda route: (outbound.append(route.request.url), route.abort()))
        page.frame_locator("iframe.kimi-artifact").locator("body").evaluate("() => window.location.assign('https://example.invalid/escape')")
        page.wait_for_timeout(200)
        assert not outbound, "Generated output navigated to an external origin"
        browser.close()
    print("Edge: generated HTML runs in a unique-origin sandbox; parent access and network configuration are isolated.")


if __name__ == "__main__":
    main()
