"""Exercise the deck in headless Edge; live calls require an explicit flag."""

import argparse
import json
import re
from pathlib import Path

from playwright.sync_api import Locator, Page, Route, expect, sync_playwright

SLIDES = 25
COMPARE, CODE_A, CODE_B, TRIAGE, MICROSOFT, IMAGE, RETAIL, PROVIDERS, OBO = "3", "5?clicks=1", "5", "6", "11", "8", "9", "12", "19"
READY = {
    "live_enabled": True, "code_run_enabled": True, "decisions_configured": True,
    "systemone_configured": True,
    "obo_configured": True, "obo_missing_settings": [],
}
BLOCKED = {
    "live_enabled": True, "code_run_enabled": False, "decisions_configured": False,
    "systemone_configured": False,
    "obo_configured": False, "obo_missing_settings": ["CLIENT_APP_ID", "AGENT_BLUEPRINT_CLIENT_ID"],
}
POST_PATHS = ("run", "decisions", "system1", "system2", "obo/start", "image-decisions", "microsoft-decision", "provider-luna", "retail-decision", "catalog-decision")
THOUGHT = "**Weighing impact**\n\nA whole team is blocked.\n\nNo account data is at risk."


def rehearse(route: Route) -> None:
    """Send the deck's live request to the adapter's synthetic test client."""
    body = json.loads(route.request.post_data or "{}")
    route.continue_(post_data=json.dumps({**body, "mode": "rehearsal"}))


def go_offline(page: Page, status: dict) -> None:
    """Stub readiness and rewrite every billable request to rehearsal."""
    page.unroute("**/demo-api/status")
    page.route("**/demo-api/status", lambda route: route.fulfill(json=status))
    for path in POST_PATHS:
        page.unroute(f"**/demo-api/{path}")
        page.route(f"**/demo-api/{path}", rehearse)


def check_layout(page: Page) -> None:
    """Require a rendered slide whose content and toolbar items fit and do not collide."""
    slide = page.locator(".slidev-layout:visible").first
    expect(slide).to_be_visible()
    expect(slide.locator(".mode-label")).to_have_count(0)
    expect(slide.get_by_role("button", name="Check connection", exact=True)).to_have_count(0)
    expect(slide).not_to_contain_text("LIVE · Azure OpenAI")
    expect(slide).not_to_contain_text("LIVE · Foundry agent")
    expect(slide).not_to_contain_text("Edit the code, then select Run.")
    overflow = slide.evaluate("""el => {
        const b = el.getBoundingClientRect();
        const out = [...el.querySelectorAll('h1,h2,p,pre,table,li,.demo,.demo-toolbar > *,.lane')]
            .filter(e => {
                const r = e.getBoundingClientRect();
                const output = e.closest('.image-output, .receiving-pipeline, .catalog-table-wrap, .catalog-inspect, .slidev-monaco-container > .flex-col');
                if (output && output !== e) {
                    // This panel intentionally scrolls long distributions and JSON.
                    const clip = output.getBoundingClientRect();
                    return r.width && (Math.min(r.right, clip.right) > b.right + 2 ||
                        Math.min(r.bottom, clip.bottom) > b.bottom + 2);
                }
                return r.width && (r.right > b.right + 2 || r.bottom > b.bottom + 2);
            }).map(e => e.textContent.slice(0, 80));
        for (const lane of el.querySelectorAll('.lane')) {
            const l = lane.getBoundingClientRect();
            for (const child of lane.children) {
                const r = child.getBoundingClientRect();
                if (r.height && r.bottom > l.bottom + 2) out.push('lane: ' + child.textContent.slice(0, 60));
            }
        }
        return out;
    }""")
    assert not overflow, f"Slide content overflow: {overflow}"
    collisions = slide.evaluate("""el => {
        const hits = [];
        for (const bar of el.querySelectorAll('.demo-toolbar')) {
            const items = [...bar.children].map(c => [c, c.getBoundingClientRect()]).filter(([, r]) => r.width);
            items.forEach(([a, ra], i) => items.slice(i + 1).forEach(([b, rb]) => {
                if (ra.left < rb.right - 1 && rb.left < ra.right - 1 && ra.top < rb.bottom - 1 && rb.top < ra.bottom - 1)
                    hits.push(`${a.textContent.slice(0, 30)} / ${b.textContent.slice(0, 30)}`);
            }));
        }
        return hits;
    }""")
    assert not collisions, f"Toolbar items overlap: {collisions}"


def visit(page: Page, base: str, slide: str) -> Locator:
    """Wait for Vue and the slide's dynamic import, then return the visible slide."""
    page.goto(f"{base}/{slide}", wait_until="domcontentloaded")
    check_layout(page)
    return page.locator(".slidev-layout:visible").first


def capture(page: Page, folder: Path | None, name: str) -> None:
    """Optionally capture an already-inspected screen."""
    if folder:
        page.screenshot(path=str(folder / name))


def choose_suitcase(slide: Locator, fixture: str) -> None:
    """Use the carousel to select a bundled scenario without triggering inference."""
    for _ in range(3):
        if slide.locator(".image-evidence img").get_attribute("src") == f"/packing/{fixture}.png":
            return
        slide.get_by_role("button", name="Next suitcase", exact=True).click()
    raise AssertionError(f"Carousel did not reach {fixture}")


def run_editor(page: Page) -> dict:
    """Select the visible Run button and return the adapter's JSON result."""
    with page.expect_response("**/demo-api/run", timeout=90000) as pending:
        page.get_by_role("button", name="Run code").click()
    response = pending.value
    assert response.status == 200, f"Run returned HTTP {response.status}"
    return response.json()


def run_compare(page: Page, timeout: int) -> tuple[dict, dict]:
    """Start both lanes with one click and return both adapter results."""
    with page.expect_response("**/demo-api/system1", timeout=timeout) as fast, \
            page.expect_response("**/demo-api/system2", timeout=timeout) as slow:
        page.get_by_role("button", name="Run both", exact=True).click()
    for pending in (fast, slow):
        assert pending.value.status == 200, f"{pending.value.url} returned HTTP {pending.value.status}"
    return fast.value.json(), slow.value.json()


def check_compare(page: Page, base: str, folder: Path | None) -> None:
    """Run System 1 and System 2 side by side, then show that one lane can fail alone."""
    slide = visit(page, base, COMPARE)
    expect(slide.get_by_role("button", name="Run both", exact=True)).to_be_enabled()
    fast, slow = run_compare(page, 30000)
    assert fast["mode"] == slow["mode"] == "rehearsal", (fast, slow)
    assert {a["name"] for a in fast["answers"]} == {"wants_refund", "team", "severity"}, fast
    lanes = slide.locator(".lane")
    expect(lanes.nth(0)).to_contain_text("refund")
    expect(lanes.nth(0)).to_contain_text("/ 4")
    expect(lanes.nth(0)).to_contain_text("output tokens")
    expect(lanes.nth(1).locator(".thinking")).to_be_visible()
    expect(lanes.nth(1).locator(".lane-answer")).not_to_be_empty()
    expect(slide.locator(".lane-cost")).to_have_count(0)
    check_layout(page)
    capture(page, folder, "slidev-compare.png")
    views = slide.get_by_role("group", name="Lane view")
    views.get_by_role("button", name="Code", exact=True).click()
    expect(lanes.nth(0).locator(".lane-code")).to_contain_text("client.decisions.create(")
    expect(lanes.nth(1).locator(".lane-code")).to_contain_text('"effort": "high"')
    check_layout(page)
    capture(page, folder, "slidev-compare-code.png")
    views.get_by_role("button", name="JSON", exact=True).click()
    expect(lanes.nth(0).locator(".lane-code")).to_contain_text('"answers"')
    expect(lanes.nth(1).locator(".lane-code")).to_contain_text('"output_text"')
    check_layout(page)
    capture(page, folder, "slidev-compare-json.png")
    views.get_by_role("button", name="Result", exact=True).click()
    page.unroute("**/demo-api/system1")
    page.unroute("**/demo-api/system2")
    page.route("**/demo-api/system1", lambda route: route.fulfill(json={**fast, "cost_usd": 0.0000456}))
    page.route("**/demo-api/system2", lambda route: route.fulfill(json={**slow, "summary": [THOUGHT], "cost_usd": 0.000162}))
    run_compare(page, 30000)
    thought = lanes.nth(1).locator(".thinking .thought").first
    expect(thought.locator("strong")).to_have_text("Weighing impact")
    expect(thought.locator("p")).to_have_count(2)
    assert thought.evaluate("""el => [...el.children].every((row, i, rows) =>
        !i || row.getBoundingClientRect().top >= rows[i - 1].getBoundingClientRect().bottom - 1)"""), \
        "Each thinking paragraph must start on its own line below the title."
    expect(lanes.nth(0).locator(".lane-cost")).to_have_text("≈ $0.046 / 1K runs")
    expect(lanes.nth(1).locator(".lane-cost")).to_have_text("≈ $0.16 / 1K runs")
    check_layout(page)
    capture(page, folder, "slidev-compare-cost.png")
    page.unroute("**/demo-api/system1")
    page.unroute("**/demo-api/system2")
    page.route("**/demo-api/system1", rehearse)
    page.route("**/demo-api/system2", rehearse)
    check_layout(page)
    slide.locator(".demo-toolbar select").select_option("security")
    expect(slide.get_by_label("Ticket text")).to_have_value(re.compile("changed my email"))
    expect(lanes.nth(0).locator(".lane-empty")).to_be_visible()
    views.get_by_role("button", name="Code", exact=True).click()
    expect(lanes.nth(0).locator(".lane-code")).to_contain_text("changed my email")
    expect(lanes.nth(1).locator(".lane-code")).to_contain_text("changed my email")
    views.get_by_role("button", name="Result", exact=True).click()
    assert page.url.endswith(f"/{COMPARE}"), "Select keys must not navigate slides."
    page.route("**/demo-api/system2", lambda route: route.abort())
    page.get_by_role("button", name="Run both", exact=True).click()
    expect(lanes.nth(1).get_by_role("alert")).to_contain_text("local demo server did not respond")
    expect(lanes.nth(0)).to_contain_text("/ 4")
    page.unroute("**/demo-api/system2")
    page.route("**/demo-api/system2", rehearse)
    check_layout(page)


def check_code_slides(page: Page, base: str, folder: Path | None) -> None:
    """Edit and run both Monaco examples through the synthetic test client."""
    slide = visit(page, base, CODE_A)
    editor = page.locator(".slidev-monaco-container:visible .view-lines").first
    expect(editor).to_be_visible(timeout=20000)
    expect(slide.locator(".run-mode")).to_have_count(0)
    editor.click()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Control+Home")
    page.keyboard.insert_text('print("edited live")\n')
    assert page.url.endswith(f"/{CODE_A}"), "Editor keys must not navigate slides."
    result = run_editor(page)
    assert result["mode"] == "rehearsal" and result["exit_code"] == 0, result
    output = page.locator(".slidev-runner-output:visible").first
    expect(output).to_contain_text("REHEARSAL")
    expect(output).to_contain_text("edited live")
    expect(output).to_contain_text('"choice": "technical"')
    check_layout(page)
    capture(page, folder, "slidev-code-three-answers.png")
    visit(page, base, CODE_B)
    expect(page.locator(".slidev-monaco-container:visible .view-lines").first).to_be_visible(timeout=20000)
    result = run_editor(page)
    assert result["exit_code"] == 0, result
    expect(page.locator(".slidev-runner-output:visible").first).to_contain_text('"probability"')
    check_layout(page)
    capture(page, folder, "slidev-code-one-predicate.png")
    page.unroute("**/demo-api/run")
    page.route("**/demo-api/run", lambda route: route.fulfill(json={
        **result, "mode": "live", "stdout": "Synthetic rendering fixture",
    }))
    run_editor(page)
    output = page.locator(".slidev-runner-output:visible").first
    expect(output).to_contain_text("Synthetic rendering fixture")
    expect(output.locator(".run-badge")).to_have_count(0)
    check_layout(page)
    page.unroute("**/demo-api/run")
    page.route("**/demo-api/run", rehearse)
    calls = []
    def track_run(request):
        if request.url.endswith("/demo-api/run"):
            calls.append(request.url)
    page.on("request", track_run)
    slide.get_by_role("button", name="Three answer shapes", exact=True).click()
    expect(page.locator(".slidev-monaco-container:visible .view-lines")).to_contain_text("teams =")
    slide.get_by_role("button", name="One predicate", exact=True).click()
    expect(page.locator(".slidev-monaco-container:visible .view-lines")).to_contain_text("I was charged twice")
    assert not calls, "Switching code stages must not run inference."
    page.remove_listener("request", track_run)


def check_triage(page: Page, base: str, folder: Path | None) -> None:
    """Run the six-question pack and move the policy threshold."""
    slide = visit(page, base, TRIAGE)
    run = page.get_by_role("button", name="Run 6 questions", exact=True)
    run.click()
    expect(slide.locator(".policy-strip")).to_contain_text("Suggested queue: billing")
    expect(slide.locator(".result-heading")).to_contain_text("billing")
    check_layout(page)
    capture(page, folder, "slidev-decisions.png")
    threshold = slide.locator("#threshold")
    threshold.focus()
    threshold.press("End")
    expect(threshold).to_have_value("0.99")
    expect(slide.locator(".policy-strip")).to_contain_text("Human review")
    assert page.url.endswith(f"/{TRIAGE}"), "Slider keys must not navigate slides."
    slide.get_by_label("Ticket evidence").fill("Different evidence")
    expect(slide.locator(".result-heading")).to_have_count(0)
    slide.get_by_label("Customer ticket").select_option("security")
    threshold.press("Home")
    run.click()
    expect(slide.locator(".policy-strip")).to_contain_text("security review")
    slide.get_by_label("Customer ticket").select_option("unclear")
    run.click()
    expect(slide.locator(".policy-strip")).to_contain_text("Human review")
    page.route("**/demo-api/decisions", lambda route: route.abort())
    run.click()
    expect(slide.get_by_role("alert")).to_contain_text("local demo server did not respond")
    expect(slide.locator(".result-heading")).to_have_count(0)
    check_layout(page)
    page.unroute("**/demo-api/decisions")
    page.route("**/demo-api/decisions", rehearse)


def check_obo(page: Page, base: str, folder: Path | None) -> None:
    """Walk sign-in, consent, continuation, and reveal with the synthetic agent."""
    slide = visit(page, base, OBO)
    expect(slide.get_by_role("button", name="Sign in & call agent", exact=True)).to_be_enabled()
    page.get_by_role("button", name="Sign in & call agent", exact=True).click()
    expect(slide.locator(".result-heading")).to_contain_text("consent required")
    expect(slide.locator(".consent-link")).to_have_count(0)
    capture(page, folder, "slidev-consent.png")
    page.get_by_role("button", name="I finished consent · continue").click()
    expect(slide.locator(".result-heading")).to_contain_text("completed")
    expect(slide.locator(".agent-response")).to_have_count(0)
    page.get_by_role("button", name="Reveal response").click()
    expect(slide.locator(".agent-response")).to_contain_text("Avery Chen")
    check_layout(page)
    capture(page, folder, "slidev-obo.png")
    page.get_by_role("button", name="Reset session", exact=True).click()
    expect(slide.locator(".result-heading")).to_have_count(0)


def check_not_connected(page: Page, base: str) -> None:
    """Show the setup step and disable each run button when the adapter is not ready."""
    go_offline(page, BLOCKED)
    for slide_number, button, message in (
        (COMPARE, "Run both", "AZURE_OPENAI_ENDPOINT"),
        (CODE_A, None, "SLIDEV_ENABLE_CODE_RUN"),
        (TRIAGE, "Run 6 questions", "AZURE_OPENAI_ENDPOINT"),
        (MICROSOFT, "Run Decision-1", "SYSTEMONE_DEPLOYMENT"),
        (IMAGE, "Inspect the suitcase", "AZURE_OPENAI_ENDPOINT"),
        (RETAIL, "Route note with Luna", "AZURE_OPENAI_ENDPOINT"),
        (PROVIDERS, "Run 12 pairs", "AZURE_OPENAI_ENDPOINT"),
        (OBO, "Sign in & call agent", "CLIENT_APP_ID"),
    ):
        slide = visit(page, base, slide_number)
        expect(slide.locator("[role=status]")).to_contain_text(message)
        if button:
            expect(page.get_by_role("button", name=button, exact=True)).to_be_disabled()
        check_layout(page)
    go_offline(page, READY)
    recovered = visit(page, base, COMPARE)
    expect(recovered.get_by_role("button", name="Run both", exact=True)).to_be_enabled()
    expect(recovered.locator(".demo-toolbar [role=status]")).to_have_count(0)


def check_new_decision_panels(page: Page, base: str, folder: Path | None) -> None:
    """Exercise native System One code and both image scenarios without Azure."""
    slide = visit(page, base, MICROSOFT)
    code = slide.get_by_label("Microsoft request code")
    expect(code).to_contain_text('"type": "noul"')
    expect(code).to_contain_text("DefaultAzureCredential")
    expect(code).to_contain_text("/providers/microsoft")
    expect(code).to_contain_text("TypeSafeClient")
    slide.get_by_role("button", name="TypeScript", exact=True).click()
    expect(slide.get_by_label("Microsoft TypeScript code")).to_contain_text("client.systemOne")
    page.get_by_role("button", name="Run Decision-1", exact=True).click()
    visual = slide.get_by_label("Microsoft visual response")
    expect(visual).to_contain_text("90.0%")
    expect(visual).to_contain_text("billing")
    expect(visual).to_contain_text("1.00")
    expect(visual.get_by_role("meter", name="Business impact score")).to_have_attribute("aria-valuemax", "3")
    bounds = slide.evaluate("""el => {
        const layout = el.getBoundingClientRect();
        const demo = el.querySelector('.microsoft-demo').getBoundingClientRect();
        const scale = layout.height / el.offsetHeight;
        const padding = parseFloat(getComputedStyle(el).paddingBottom) * scale;
        return { actual: demo.bottom, expected: layout.bottom - padding };
    }""")
    assert abs(bounds["actual"] - bounds["expected"]) < 2, bounds
    slide.get_by_role("button", name="JSON", exact=True).click()
    expect(slide.get_by_label("Microsoft response JSON")).to_contain_text('"answers": {')
    expect(slide).to_contain_text("REHEARSAL")
    check_layout(page)
    capture(page, folder, "slidev-microsoft-decision.png")
    slide.get_by_label("Microsoft decision ticket").fill("Every checkout request fails.")
    expect(visual).to_have_count(0)
    slide.get_by_role("button", name="Python", exact=True).click()
    expect(code).to_contain_text("Every checkout request fails.")
    page.route("**/demo-api/microsoft-decision", lambda route: route.abort())
    slide.get_by_role("button", name="Run Decision-1", exact=True).click()
    expect(slide.get_by_role("alert")).to_contain_text("local demo server did not respond")
    expect(slide.get_by_label("Microsoft response JSON")).to_have_count(0)
    page.unroute("**/demo-api/microsoft-decision")
    page.route("**/demo-api/microsoft-decision", rehearse)
    page.route("**/demo-api/microsoft-code", lambda route: route.abort())
    slide.get_by_label("Microsoft decision ticket").fill("A changed ticket with an unavailable preview.")
    slide.get_by_role("button", name="Python", exact=True).click()
    expect(code).to_be_empty()
    slide.get_by_role("button", name="TypeScript", exact=True).click()
    expect(slide.get_by_label("Microsoft TypeScript code")).to_be_empty()
    expect(slide.get_by_role("alert")).to_contain_text("local demo server did not respond")
    page.unroute("**/demo-api/microsoft-code")
    for with_brief in (False, True):
        slide = visit(page, base, IMAGE)
        if with_brief:
            slide.get_by_role("button", name="Add a trip brief", exact=True).click()
        run_name = "Decide for this trip" if with_brief else "Inspect the suitcase"
        if not with_brief:
            expect(slide).to_contain_text("Instructions sent to the model")
            expect(slide).to_contain_text("A hat or ordinary shirt is not rain protection.")
            expect(slide.locator(".packing-objective > div")).to_have_count(3)
            expect(slide.locator(".packing-objective dt span")).to_have_text(["PREDICATE", "CHOICE", "CHOICE"])
            expect(slide).not_to_contain_text("Edit a question's instructions beneath the image")
            expect(slide).not_to_contain_text("AI-generated photorealistic fixture")
            expect(slide).not_to_contain_text("What can you actually see?")
            expect(slide.locator(".packing-foot")).to_have_count(0)
            editor = slide.get_by_label("Inspection instructions", exact=True)
            expect(editor).to_have_value(re.compile("Is an umbrella"))
            editor.fill("Is a yellow hooded raincoat visible? Ignore umbrellas.")
            slide.get_by_role("button", name="Python", exact=True).click()
            expect(slide.get_by_label("Image request code")).to_contain_text("yellow hooded raincoat")
            slide.get_by_role("button", name="Answers", exact=True).click()
            with page.expect_request("**/demo-api/image-decisions") as pending:
                slide.get_by_role("button", name=run_name, exact=True).click()
            assert pending.value.post_data_json["instructions"]["rain_protection"].endswith("Ignore umbrellas.")
            expect(slide.locator(".image-answer")).to_have_count(3)
            slide.get_by_label("Inspection question", exact=True).select_option("footwear")
            expect(editor).to_have_value(re.compile("Which footwear"))
            editor.fill("Identify visible footwear only.")
            expect(slide.locator(".image-answer")).to_have_count(0)
            slide.get_by_label("Inspection question", exact=True).select_option("rain_protection")
            expect(editor).to_have_value("Is a yellow hooded raincoat visible? Ignore umbrellas.")
        for fixture in ("sunshine", "rain", "obscured"):
            choose_suitcase(slide, fixture)
            image = slide.locator(".image-evidence img")
            expect(image).to_have_attribute("src", f"/packing/{fixture}.png")
            expect(image).to_be_visible()
            assert image.evaluate("""async el => {
                await el.decode()
                return el.naturalWidth === 1536 && el.naturalHeight === 1024
            }""")
            if not with_brief:
                ratio = image.evaluate("el => { const r = el.getBoundingClientRect(); return r.width / r.height }")
                assert abs(ratio - 1.5) < 0.01, f"Suitcase image must keep its 3:2 ratio: {ratio}"
                assert slide.evaluate("""el => {
                    const box = el.getBoundingClientRect()
                    const scale = box.height / el.offsetHeight
                    const bottom = box.bottom - parseFloat(getComputedStyle(el).paddingBottom) * scale
                    return ['.image-evidence > .primary', '.image-output'].every(selector =>
                        Math.abs(el.querySelector(selector).getBoundingClientRect().bottom - bottom) < 2)
                }"""), "Both suitcase columns must reach the bottom padding"
                assert slide.locator(".image-evidence").evaluate("""el => {
                    const bottom = el.getBoundingClientRect().bottom
                    return [...el.children].every(child => child.getBoundingClientRect().bottom <= bottom + 1)
                }"""), "Suitcase controls must fit below the image"
            slide.get_by_role("button", name=run_name, exact=True).click()
            expect(slide.locator(".image-answer")).to_have_count(4 if with_brief else 3)
            expect(slide).to_contain_text("REHEARSAL")
            slide.get_by_role("button", name="Python", exact=True).click()
            expect(slide.get_by_label("Image request code")).to_contain_text(f"{fixture}.png")
            expect(slide.get_by_label("Image request code")).to_contain_text("base64.b64encode")
            slide.get_by_role("button", name="JSON", exact=True).click()
            expect(slide.get_by_label("Image response JSON")).to_contain_text('"answers"')
            slide.get_by_role("button", name="Answers", exact=True).click()
            check_layout(page)
        if with_brief:
            slide.get_by_role("button", name="Plot twist: rain", exact=True).click()
            expect(slide.locator(".image-answer")).to_have_count(0)
            slide.get_by_role("button", name="Python", exact=True).click()
            expect(slide.get_by_label("Image request code")).to_contain_text("cold, rainy outdoor")
            expect(slide.get_by_label("Image request code")).to_contain_text("def packing_route")
            slide.get_by_role("button", name="Answers", exact=True).click()
            slide.get_by_label("Trip brief").fill("A rainy photography walk.")
            expect(slide.locator(".image-answer")).to_have_count(0)
            # Use explicit rendering fixtures to exercise every application route;
            # these are not image-model accuracy assertions.
            for label, score, quality in (("ready", 1.8, "clear"), ("repack", 0.3, "clear"),
                                          ("review", 1.8, "obscured")):
                answers = [
                    {"type": "choice", "name": "evidence_quality", "choice": quality, "confidence": 0.9,
                     "probabilities": [{"value": "clear", "probability": 0.9}, {"value": "obscured", "probability": 0.1}]},
                    {"type": "score", "name": "trip_fit", "score": score, "confidence": 0.9,
                     "probabilities": [{"value": 0, "label": "mismatch", "probability": 0.1},
                                       {"value": 1, "label": "partial", "probability": 0.1},
                                       {"value": 2, "label": "suited", "probability": 0.8}]},
                ]
                payload = {"mode": "rehearsal", "elapsed_ms": None,
                           "raw": {"model": "synthetic", "answers": answers,
                                   "usage": {"input_tokens": 100, "output_tokens": 0}},
                           "route": {"label": label, "reason": "Synthetic rendering fixture"}}
                page.unroute("**/demo-api/image-decisions")
                page.route("**/demo-api/image-decisions", lambda route: route.fulfill(json=payload))
                slide.get_by_role("button", name=run_name, exact=True).click()
                expect(slide.locator(".packing-route")).to_have_attribute("data-route", label)
                expect(slide.locator("meter")).to_have_count(5)
                check_layout(page)
                if label == "ready":
                    capture(page, folder, "slidev-packing-result.png")
            page.unroute("**/demo-api/image-decisions")
            page.route("**/demo-api/image-decisions", rehearse)
            slide.get_by_label("Trip brief").fill("")
            expect(slide.get_by_role("button", name=run_name, exact=True)).to_be_disabled()
            slide.get_by_role("button", name="Beach weekend", exact=True).click()
            expect(slide.locator(".packing-route")).to_have_count(0)
        capture(page, folder, f"slidev-image-{'brief' if with_brief else 'visual'}.png")
        page.route("**/demo-api/image-decisions", lambda route: route.abort())
        slide.get_by_role("button", name=run_name, exact=True).click()
        expect(slide.get_by_role("alert")).to_contain_text("local demo server did not respond")
        expect(slide.locator(".image-answer")).to_have_count(0)
        check_layout(page)
        page.unroute("**/demo-api/image-decisions")
        page.route("**/demo-api/image-decisions", rehearse)
        image_source = slide.locator(".image-evidence img").get_attribute("src")
        slide.get_by_role("button", name="Inspect the image" if with_brief else "Add a trip brief", exact=True).click()
        expect(slide.locator(".image-evidence img")).to_have_attribute("src", image_source)
        expect(slide.locator(".image-answer")).to_have_count(0)
        expect(slide.get_by_role("button", name="Inspect the suitcase" if with_brief else "Decide for this trip", exact=True)).to_be_enabled()


def check_retail_and_providers(page: Page, base: str, folder: Path | None) -> None:
    """Verify no-model evidence gates and independent provider lanes without Azure."""
    slide = visit(page, base, RETAIL)
    expect(slide).to_contain_text("USD 37.00")
    expect(slide).to_contain_text("no live OCR / DI / CU call")
    run = slide.get_by_role("button", name="Route note with Luna", exact=True)
    expect(run).to_be_enabled()
    run.focus()
    page.keyboard.press("Enter")
    expect(slide).to_contain_text("REHEARSAL")
    slide.get_by_role("button", name="JSON", exact=True).click()
    expect(slide.get_by_label("Retail evidence and decision JSON")).to_contain_text('"source_regions"')
    slide.get_by_role("button", name="Evidence → route", exact=True).click()
    for fixture, text in (("low_ocr", "Low or missing OCR confidence"),
                          ("missing_region", "Missing or invalid source region"),
                          ("contradiction", "contradict each other"),
                          ("reason_code", "Skip the model")):
        slide.get_by_label("Receiving scenario").select_option(fixture)
        expect(slide).to_contain_text(text)
        expect(run).to_be_disabled()
        expect(slide).not_to_contain_text("REHEARSAL")
        check_layout(page)
    capture(page, folder, "retail-no-model-path.png")
    slide.get_by_label("Receiving scenario").select_option("clear")
    expect(run).to_be_enabled()
    page.route("**/demo-api/retail-decision", lambda route: route.abort())
    run.focus()
    page.keyboard.press("Enter")
    expect(slide.get_by_role("alert")).to_contain_text("local demo server did not respond")
    page.unroute("**/demo-api/retail-decision")
    page.route("**/demo-api/retail-decision", rehearse)
    check_layout(page)

    slide = visit(page, base, PROVIDERS)
    run_both = slide.get_by_role("button", name="Run 12 pairs", exact=True)
    expect(run_both).to_be_enabled()
    expect(slide.locator(".catalog-product img")).to_have_count(2)
    assert slide.locator(".catalog-product img").evaluate_all("(images) => images.every(img => img.complete && img.naturalWidth > 0)")
    slide.get_by_role("button", name="Request", exact=True).click()
    expect(slide.get_by_label("luna request")).to_contain_text('"choices"')
    expect(slide.get_by_label("microsoft request")).to_contain_text('"criteria"')
    check_layout(page)
    run_both.click()
    for lane in slide.locator(".catalog-lane").all():
        expect(lane).to_have_attribute("aria-busy", "false", timeout=60000)
        expect(lane).to_contain_text("12 / 12 processed")
        expect(lane).to_contain_text("12 / 12 reference matches")
    expect(slide.locator(".catalog-table .matched")).to_have_count(24)
    assert slide.locator(".catalog-table-wrap").evaluate("el => el.scrollHeight <= el.clientHeight + 1"), "All 12 pairs must fit without scrolling"
    expect(slide).to_contain_text("REHEARSAL")
    check_layout(page)
    capture(page, folder, "catalog-batch-comparison.png")
    slide.get_by_role("button", name="2. Same laptop, more storage", exact=True).click()
    expect(slide.locator(".catalog-reference")).to_contain_text("Reference: Different")
    expect(slide.locator(".attribute-diff")).to_contain_text(["storage512 GB", "storage1 TB"])
    slide.get_by_role("button", name="JSON", exact=True).click()
    expect(slide.get_by_label("luna native JSON")).to_contain_text('"answers": [')
    expect(slide.get_by_label("microsoft native JSON")).to_contain_text('"answers": {')
    slide.get_by_label("Inspect product pair").select_option("3")
    expect(slide.locator(".catalog-reference")).to_contain_text("Reference: Review")
    assert slide.locator(".catalog-reference").evaluate("""el =>
        el.getBoundingClientRect().bottom <
        document.querySelector('.catalog-disclaimer').getBoundingClientRect().top"""), "Reference must not overlap the footer"
    check_layout(page)


def check_provider_timers(page: Page, base: str) -> None:
    """Verify series order, equal work, no timer jump, quality, unknown costs, and errors."""
    slide = visit(page, base, PROVIDERS)
    fixtures = page.request.get(f"{base}/demo-api/catalog-fixtures", headers={"X-Demo-Client": "slidev"}).json()["pairs"]
    held: dict[str, Route] = {}
    seen: dict[str, list[str]] = {"luna": [], "microsoft": []}
    def hold(route: Route) -> None:
        body = route.request.post_data_json
        provider = body["provider"]
        assert provider not in held, "More than one in-flight request in a provider lane"
        seen[provider].append(body["pair"])
        held[provider] = route
    page.route("**/demo-api/catalog-decision", hold)
    lanes = slide.locator(".catalog-lane")
    clocks = slide.locator(".run-clock")
    run = slide.get_by_role("button", name="Run 12 pairs", exact=True)
    def wait_held(provider: str) -> Route:
        for _ in range(100):
            if provider in held:
                return held.pop(provider)
            page.wait_for_timeout(20)
        raise AssertionError(f"No request arrived for {provider}")
    def milliseconds(text: str) -> float:
        return float(text.split()[0]) * (1000 if text.endswith(" s") else 1)
    def fulfill(provider: str, index: int, answer: str | None = None, cost: float | None = .000042) -> None:
        item = {"type": "choice", "choice": answer or fixtures[index]["expected"]}
        answers = [{**item, "name": "match"}] if provider == "luna" else {"match": item}
        wait_held(provider).fulfill(json={"mode": "live", "elapsed_ms": 898, "cost_usd": cost,
                                        "raw": {"answers": answers}})
    try:
        run.click()
        for lane in (lanes.nth(0), lanes.nth(1)):
            expect(lane).to_have_attribute("aria-busy", "true")
            expect(lane.locator(".timing-label")).to_have_text("Total elapsed")
            expect(lane.locator(".run-clock")).not_to_have_text("0 ms")
        for index in range(12):
            fulfill("luna", index, "different" if index == 0 else None)
        expect(lanes.nth(0)).to_have_attribute("aria-busy", "false")
        expect(lanes.nth(0)).to_contain_text("11 / 12 reference matches")
        expect(lanes.nth(0)).to_contain_text("≈ $0.042 / 1K pairs")
        frozen_luna = clocks.nth(0).inner_text()
        expect(lanes.nth(1)).to_have_attribute("aria-busy", "true")
        assert seen["microsoft"] == [fixtures[0]["id"]]
        page.wait_for_function("""() => {
            const el = document.querySelectorAll('.provider-slide .run-clock')[1];
            return el.textContent.endsWith(' s') && parseFloat(el.textContent) >= 4.2;
        }""", timeout=10000)
        before = clocks.nth(1).inner_text()
        for index in range(12):
            fulfill("microsoft", index, cost=None if index == 3 else .000042)
        expect(lanes.nth(1)).to_have_attribute("aria-busy", "false")
        assert milliseconds(clocks.nth(1).inner_text()) >= milliseconds(before) >= 4200
        expect(lanes.nth(1)).to_contain_text("Cost unavailable")
        expect(clocks.nth(0)).to_have_text(frozen_luna)
        assert seen["luna"] == seen["microsoft"] == [entry["id"] for entry in fixtures]
        expect(slide.locator(".catalog-table .mismatch")).to_have_count(1)
        check_layout(page)
        seen = {"luna": [], "microsoft": []}
        run.click()
        expect(slide.locator(".api-timing")).to_have_count(0)
        expect(slide.locator(".catalog-table .matched")).to_have_count(0)
        for index in range(12):
            for provider in ("luna", "microsoft"):
                if index == 0:
                    wait_held(provider).abort()
                elif index == 1:
                    wait_held(provider).fulfill(json={"mode": "live", "elapsed_ms": 10, "cost_usd": .1,
                                                     "raw": {"answers": {}}})
                elif index == 2:
                    answer = {"type": "refusal"}
                    answers = [{**answer, "name": "match"}] if provider == "luna" else {"match": answer}
                    wait_held(provider).fulfill(json={"mode": "live", "elapsed_ms": 10, "cost_usd": .1,
                                                     "raw": {"answers": answers}})
                else:
                    fulfill(provider, index)
        for lane in lanes.all():
            expect(lane).to_have_attribute("aria-busy", "false")
            expect(lane).to_contain_text("9 / 12 reference matches")
            expect(lane).to_contain_text("Cost unavailable")
        expect(slide.locator(".catalog-table")).to_contain_text("Refused")
        expect(slide.locator(".catalog-table")).to_contain_text("Invalid")
        slide.get_by_role("button", name="JSON", exact=True).click()
        expect(slide.get_by_role("alert").filter(has_text="local demo server did not respond")).to_have_count(2)
        check_layout(page)
    finally:
        for route in held.values():
            route.abort()
        page.unroute("**/demo-api/catalog-decision")
        page.route("**/demo-api/catalog-decision", rehearse)


def check_live_compare(page: Page, base: str, folder: Path | None) -> None:
    """Run both lanes once against the configured deployment."""
    slide = visit(page, base, COMPARE)
    expect(slide.get_by_role("button", name="Run both", exact=True)).to_be_enabled(timeout=20000)
    fast, slow = run_compare(page, 240000)
    assert fast["mode"] == slow["mode"] == "live", "A live failure must never become a mock result."
    assert len(fast["answers"]) == 3 and slow["text"].strip(), (fast, slow)
    assert fast["elapsed_ms"] > 0 and slow["elapsed_ms"] > 0
    expect(slide.locator(".lane-clock").nth(0)).to_contain_text(" s")
    expect(slide.locator(".lane-clock").nth(1)).to_contain_text(" s")
    expect(slide.locator(".lane-cost")).to_have_count(2)
    assert fast["cost_usd"] > 0 and slow["cost_usd"] > 0, (fast["cost_usd"], slow["cost_usd"])
    assert fast["raw"]["answers"] and slow["raw"]["output"], "The JSON view needs each raw response body."
    check_layout(page)
    capture(page, folder, "slidev-live-compare.png")
    print(f"PASS live compare: System 1 {fast['elapsed_ms']} ms, {fast['usage']['output_tokens']} output tokens, "
          f"${fast['cost_usd']:.6f}; System 2 {slow['elapsed_ms']} ms, {slow['usage']['output_tokens']} output tokens "
          f"({slow['usage']['reasoning_tokens']} reasoning), ${slow['cost_usd']:.6f}, {len(slow['summary'])} summary parts.")
    if folder:
        (folder / "slidev-live-compare.json").write_text(json.dumps({"system1": fast, "system2": slow}, indent=2), encoding="utf-8")


def check_live_code(page: Page, base: str, folder: Path | None) -> None:
    """Run each Monaco slide once against the configured Azure OpenAI deployment."""
    results = []
    for slide_number in (CODE_A, CODE_B):
        slide = visit(page, base, slide_number)
        expect(slide.locator(".run-mode")).to_have_count(0, timeout=20000)
        result = run_editor(page)
        assert result["mode"] == "live", "A live failure must never become a mock result."
        assert result["exit_code"] == 0, result["stderr"]
        assert "MockClient" not in result["stdout"]
        expect(page.locator(".slidev-runner-output:visible .run-badge")).to_have_count(0)
        check_layout(page)
        capture(page, folder, f"slidev-live-code-{slide_number}.png")
        results.append({"slide": slide_number, **result})
        print(f"PASS live code slide {slide_number}: {result['model']}\n{result['stdout'].strip()}")
    if folder:
        (folder / "slidev-live-code.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


def check_live_decisions(page: Page, base: str, folder: Path | None) -> None:
    """Send two synthetic tickets through the real Vue-to-Azure path."""
    slide = visit(page, base, TRIAGE)
    expect(slide.get_by_role("button", name="Run 6 questions", exact=True)).to_be_enabled(timeout=20000)
    results = []
    for ticket, department in (("refund", "billing"), ("security", "security")):
        slide.get_by_label("Customer ticket").select_option(ticket)
        with page.expect_response("**/demo-api/decisions", timeout=90000) as pending:
            page.get_by_role("button", name="Run 6 questions", exact=True).click()
        response = pending.value
        assert response.status == 200, f"Live API returned HTTP {response.status}"
        result = response.json()
        assert result["mode"] == "live", "A live failure must never become a mock result."
        assert len(result["answers"]) == 6
        answer = next(a for a in result["answers"] if a["name"] == "department")
        assert answer["type"] == "choice" and answer["choice"] == department
        assert isinstance(result["elapsed_ms"], int) and result["elapsed_ms"] > 0
        expect(slide.locator(".result-heading")).to_contain_text(department)
        expect(slide.locator(".result-heading")).to_contain_text("ms")
        check_layout(page)
        capture(page, folder, f"slidev-live-{ticket}.png")
        results.append({"ticket": ticket, **result})
        print(f"PASS live Decisions: {ticket} -> {department}; {len(result['answers'])} answers, {result['elapsed_ms']} ms.")
    if folder:
        (folder / "slidev-live-decisions.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


def check_live_packing(page: Page, base: str, folder: Path | None) -> None:
    """Rehearse synthetic photographs through Vue, the adapter, and live Azure Decisions."""
    slide = visit(page, base, IMAGE)
    with page.expect_response("**/demo-api/image-decisions", timeout=240000) as pending:
        slide.get_by_role("button", name="Inspect the suitcase", exact=True).click()
    assert pending.value.status == 200, pending.value.text()
    visual = pending.value.json()
    assert visual["mode"] == "live" and visual["route"] is None
    assert len(visual["raw"]["answers"]) == 3
    capture(page, folder, "slidev-packing-live-visual.png")
    results = [{"fixture": "sunshine", "context": "visual", **visual}]
    scores = []
    slide = visit(page, base, IMAGE)
    slide.get_by_role("button", name="Add a trip brief", exact=True).click()
    for fixture, preset in (("sunshine", "Beach weekend"), ("sunshine", "Plot twist: rain"),
                            ("rain", "Plot twist: rain"), ("obscured", "Plot twist: rain")):
        choose_suitcase(slide, fixture)
        slide.get_by_role("button", name=preset, exact=True).click()
        with page.expect_response("**/demo-api/image-decisions", timeout=240000) as pending:
            slide.get_by_role("button", name="Decide for this trip", exact=True).click()
        response = pending.value
        assert response.status == 200, response.text()
        result = response.json()
        assert result["mode"] == "live" and result["elapsed_ms"] > 0
        expect(slide.locator(".packing-route")).to_have_attribute("data-route", result["route"]["label"])
        if fixture == "sunshine":
            fit = next(a for a in result["raw"]["answers"] if a["name"] == "trip_fit")
            assert fit["type"] == "score", fit
            scores.append(fit["score"])
        if fixture == "obscured":
            assert result["route"]["label"] == "review", result
        check_layout(page)
        capture(page, folder, f"slidev-packing-live-{fixture}-{'beach' if preset == 'Beach weekend' else 'rain'}.png")
        results.append({"fixture": fixture, "brief": preset, **result})
        print(f"LIVE packing {fixture} / {preset}: {result['route']['label']}, {result['elapsed_ms']} ms")
    if folder:
        (folder / "slidev-live-packing.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    assert scores[0] > scores[1], f"The beach/rain contrast was not observed: {scores}"


def check_color_modes(browser, base: str, folder: Path | None) -> None:
    """Verify system theme changes and readable text on custom demo surfaces."""
    context = browser.new_context(viewport={"width": 1280, "height": 720}, color_scheme="light")
    context.add_init_script("localStorage.setItem('slidev-color-schema', 'auto')")
    page = context.new_page()
    go_offline(page, READY)
    try:
        for mode in ("light", "dark"):
            page.emulate_media(color_scheme=mode)
            for number in ("1", COMPARE, CODE_A, TRIAGE, MICROSOFT, IMAGE, RETAIL, PROVIDERS, OBO):
                slide = visit(page, base, number)
                expect(page.locator("html")).to_have_class(re.compile(rf"\b{mode}\b"))
                contrast = slide.evaluate("""el => {
                    const luminance = color => {
                        const rgb = color.match(/[\\d.]+/g).slice(0, 3).map(Number)
                            .map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4 });
                        return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
                    };
                    const nodes = [el, ...el.querySelectorAll('textarea,select,.primary,.view-switch button[aria-pressed="true"],.lane-code,.native-code')];
                    return nodes.filter(n => {
                        const r = n.getBoundingClientRect();
                        return r.width > 2 && r.height > 2 && !n.closest('.monaco-editor');
                    }).map(n => {
                        const s = getComputedStyle(n);
                        const a = luminance(s.color), b = luminance(s.backgroundColor);
                        return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
                    });
                }""")
                assert all(value >= 4.5 for value in contrast), (mode, number, contrast)
                if number == COMPARE:
                    capture(page, folder, f"slidev-compare-{mode}.png")
        page.emulate_media(color_scheme="light")
        expect(page.locator("html")).to_have_class(re.compile(r"\blight\b"))
        print("PASS automatic light/dark switching and text contrast across demo surfaces.")
    finally:
        context.close()


def main() -> None:
    """Check every slide, each live panel's flow, presenter notes, and failure states."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:3030")
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--live-decisions", action="store_true", help="Make billable Azure OpenAI calls with synthetic text: one System 1 and System 2 run, two triage runs, and one code run on each Monaco slide. Does not invoke live OBO.")
    parser.add_argument("--live-packing", action="store_true", help="Make five billable Azure Decisions calls using the synthetic suitcase photos. Never invokes OBO.")
    args = parser.parse_args()
    if args.capture_dir:
        args.capture_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        try:
            check_color_modes(browser, args.url, args.capture_dir)
            for width, height in ((1920, 1080), (1280, 720)):
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                folder = args.capture_dir if width == 1920 else None
                go_offline(page, READY)
                for number in range(1, SLIDES + 1):
                    visit(page, args.url, str(number))
                check_compare(page, args.url, folder)
                check_code_slides(page, args.url, folder)
                check_triage(page, args.url, folder)
                check_new_decision_panels(page, args.url, folder)
                check_retail_and_providers(page, args.url, folder)
                check_provider_timers(page, args.url)
                check_obo(page, args.url, folder)
                check_not_connected(page, args.url)
                assert not errors, errors
                print(f"PASS {width}x{height}: {SLIDES} slides, System 1 and 2 compare, editable code runs, triage, Microsoft-Decision-1, images, OBO, not-connected states, and API failure.")
                context.close()

            page = browser.new_page()
            page.goto(f"{args.url}/presenter/1")
            page.wait_for_load_state("networkidle")
            expect(page.get_by_text(re.compile("Start with the practical difference"))).to_be_visible()
            print("PASS presenter notes.")
            if args.live_decisions:
                page.set_viewport_size({"width": 1920, "height": 1080})
                check_live_compare(page, args.url, args.capture_dir)
                check_live_decisions(page, args.url, args.capture_dir)
                check_live_code(page, args.url, args.capture_dir)
            if args.live_packing:
                page.set_viewport_size({"width": 1920, "height": 1080})
                check_live_packing(page, args.url, args.capture_dir)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
