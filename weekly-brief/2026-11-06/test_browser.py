"""Check every slide and presenter note in Microsoft Edge, without cloud calls."""

import argparse
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright


def notes_from_source() -> list[str]:
    text = Path(__file__).with_name("slides.md").read_text(encoding="utf-8")
    notes = re.findall(r"<!--\s*(.*?)\s*-->", text, re.S)
    assert len(notes) >= 24, f"Expected complete baseline coverage, got {len(notes)} notes"
    for index, note in enumerate(notes, 1):
        speech = re.split(r"\n\s*Sources?,", note)[0]
        count = len(speech.split())
        assert 60 <= count <= 120, (index, count)
        assert "https://" in note, f"Slide {index} has no first-party source URL"
        assert re.search(r"2026-\d\d-\d\d", note), f"Slide {index} has no dated source"
    return notes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url", default="http://127.0.0.1:3080")
    parser.add_argument("--phase", default="baseline")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    notes = notes_from_source()
    evidence = []
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        context.add_init_script("""localStorage.setItem('slidev-sync-directions', JSON.stringify({
          viewerSend:false, viewerReceive:false, presenterSend:false, presenterReceive:false
        }))""")
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        for width, height in [(1280, 720), (1920, 1080)]:
            page.set_viewport_size({"width": width, "height": height})
            for theme in ["light", "dark"]:
                page.emulate_media(color_scheme=theme, reduced_motion="reduce")
                for slide in range(1, len(notes) + 1):
                    page.goto(f"{args.url}/{slide}", wait_until="networkidle", timeout=90_000)
                    page.evaluate("(dark) => document.documentElement.classList.toggle('dark', dark)", theme == "dark")
                    root = page.locator(".slidev-page").filter(visible=True).first
                    root.wait_for()
                    page.wait_for_timeout(100)
                    layout = root.evaluate("""root => {
                      const slide = root.querySelector('.slidev-layout') || root;
                      const box = slide.getBoundingClientRect();
                      const defects = [];
                      const clips = node => {
                        for (let p=node.parentElement; p && p!==slide; p=p.parentElement) {
                          const css=getComputedStyle(p);
                          if (/(auto|scroll)/.test(css.overflow+css.overflowX+css.overflowY)) return true;
                        }
                        return false;
                      };
                      for (const node of slide.querySelectorAll('h1,h2,p,table,svg,button,figure,.brief-window,.brief-quad,.brief-cards,.brief-migrations')) {
                        if (!node.checkVisibility() || clips(node)) continue;
                        const r=node.getBoundingClientRect();
                        if (r.left<box.left-2 || r.right>box.right+2 || r.bottom>box.bottom+2 || r.top<box.top-2)
                          defects.push({tag:node.tagName,text:node.textContent.slice(0,100),x:r.x,y:r.y,w:r.width,h:r.height});
                      }
                      const walker=document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
                      while(walker.nextNode()) {
                        const text=walker.currentNode, node=text.parentElement;
                        if(!text.textContent.trim() || !node || !node.checkVisibility() || clips(node)) continue;
                        const range=document.createRange(); range.selectNodeContents(text);
                        const r=range.getBoundingClientRect();
                        if(!r.width || !r.height) continue;
                        let boundary=box;
                        for(let p=node; p && p!==slide; p=p.parentElement) {
                          const css=getComputedStyle(p);
                          if(/(hidden|clip)/.test(css.overflow+css.overflowX+css.overflowY)) {
                            const clip=p.getBoundingClientRect();
                            boundary={left:Math.max(boundary.left,clip.left),right:Math.min(boundary.right,clip.right),
                              top:Math.max(boundary.top,clip.top),bottom:Math.min(boundary.bottom,clip.bottom)};
                          }
                        }
                        if(r.left<boundary.left-2 || r.right>boundary.right+2 || r.top<boundary.top-2 || r.bottom>boundary.bottom+2)
                          defects.push({tag:'text',text:text.textContent.slice(0,100),x:r.x,y:r.y,w:r.width,h:r.height});
                      }
                      return {width:box.width,height:box.height,defects,text:slide.innerText};
                    }""")
                    page.screenshot(path=str(args.output / f"{args.phase}-{slide:02d}-{theme}-{width}.png"))
                    evidence.append({"slide": slide, "theme": theme, "width": width, "layout": layout})
        # Check all notes in the actual presenter surface, not only Markdown comments.
        page.set_viewport_size({"width": 1920, "height": 1080})
        for index, note in enumerate(notes, 1):
            page.goto(f"{args.url}/presenter/{index}", wait_until="networkidle", timeout=90_000)
            phrase = " ".join(note.split()[:10])
            page.wait_for_function(
                "phrase => document.body.innerText.replace(/\\s+/g,' ').includes(phrase)",
                arg=phrase, timeout=15_000,
            )
            evidence.append({"presenter_slide": index, "notes_visible": True})
        page.screenshot(path=str(args.output / f"{args.phase}-presenter.png"))
        page.goto(f"{args.url}/13", wait_until="networkidle")
        page.get_by_role("button", name="Check final state", exact=True).click()
        page.get_by_text("report.csv is missing", exact=True).wait_for()
        page.screenshot(path=str(args.output / f"{args.phase}-verified-state-interaction.png"))
        browser.close()
    defects = [row for row in evidence if row.get("layout", {}).get("defects")]
    result = {"browser": "Microsoft Edge", "slides": len(notes), "captures": len(notes) * 4,
              "evidence": evidence, "errors": errors, "overflow_count": len(defects)}
    (args.output / f"{args.phase}-evidence.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert not defects, json.dumps(defects, indent=2)
    assert not errors, "\n".join(errors)
    print(f"Edge: all {len(notes)} slides, 96 theme/resolution captures, all presenter notes visible; no overflow or runtime errors.")


if __name__ == "__main__":
    main()
