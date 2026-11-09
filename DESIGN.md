---
name: Handoff Slidev
description: A calm, first-party briefing system for live developer demos.
colors:
  workbench-paper: "#f4f6f8"
  clean-sheet: "#ffffff"
  cobalt-wash: "#dce9ff"
  muted-stock: "#e8edf3"
  bench-ink: "#101820"
  graphite: "#475461"
  drafting-rule: "#c8d0d8"
  cobalt-mark: "#0759d6"
  deep-cobalt: "#003a9e"
  control-stroke: "#687889"
  live-signal-amber: "#db8a19"
  late-night-stage: "#0b1026"
  chalk-lettering: "#ecf1ff"
  stage-haze: "#c5d1ff"
  banner-indigo: "#4e52b9"
  stage-line: "#5864b7"
  night-workbench: "#10161d"
  night-sheet: "#161e27"
  night-cobalt-wash: "#182c4e"
  night-stock: "#1d2937"
  night-ink: "#f1f5f9"
  night-graphite: "#aab7c4"
  night-rule: "#354352"
  night-cobalt-mark: "#68a1ff"
  night-deep-cobalt: "#a9c7ff"
  night-control-stroke: "#71859c"
  night-live-amber: "#f0a439"
typography:
  display:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "78px"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "-.025em"
  headline:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "52px"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-.02em"
  title:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1.25
  lede:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "29px"
    fontWeight: 400
    lineHeight: 1.45
  body:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "24px"
    fontWeight: 400
    lineHeight: 1.45
  table:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "23px"
    fontWeight: 400
    lineHeight: 1.45
  comparison:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "21px"
    fontWeight: 400
    lineHeight: 1.45
  caption:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.45
  code:
    fontFamily: "IBM Plex Mono, Cascadia Code, monospace"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.48
  compact:
    fontFamily: "IBM Plex Mono, Cascadia Code, monospace"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.45
  comparison-emphasis:
    fontFamily: "IBM Plex Sans, Segoe UI, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.45
  label:
    fontFamily: "IBM Plex Mono, Cascadia Code, monospace"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.3
rounded:
  control: "8px"
  panel: "12px"
spacing:
  "1": "8px"
  "2": "16px"
  "3": "24px"
  "4": "32px"
  "5": "40px"
  "6": "48px"
components:
  button-primary:
    backgroundColor: "{colors.cobalt-mark}"
    textColor: "{colors.clean-sheet}"
    rounded: "{rounded.control}"
    padding: "10px 15px"
    typography: "700 18px/1.35 IBM Plex Sans, Segoe UI, sans-serif"
  button-primary-hover:
    backgroundColor: "{colors.deep-cobalt}"
---

# Design System: Handoff Slidev

## Overview

**Creative North Star: "The Product Briefing"**

A calm, dev-focused, first-party educational briefing: one point per slide. Let demos do the talking. Use less text and more graphics, illustrations, cards, and embedded mini-apps to inform the audience. The voice is authoritative and unmistakably first-party Foundry, while the visual language stays precise and approachable.

The shared system gives both Decisions and copilot-harness a light workbench for explanation and a persistent navy stage for emphasis. Shared typography, semantic CSS classes, and a restrained cobalt signal make the decks feel like one briefing without making live demos look like static slides.

**Key Characteristics:**
- One point per slide; demos lead.
- Calm workbench and deep-navy stage.
- Flat, projector-clear surfaces; live state is explicit.

### Named Rules
**The One Point Rule.** Give each slide one clear idea; let the demo carry detail.

**The Demo Does the Talking Rule.** Favor graphics, cards, and embedded mini-apps over explanatory text blocks.

## Colors

The palette pairs cool workbench neutrals and cobalt structure with a shared navy stage; amber is reserved for live state.

### Primary
- **Cobalt Mark** (`#0759d6`): Light-theme actions, links, focus, and structural emphasis.
- **Deep Cobalt** (`#003a9e`): Light-theme hover and pressed emphasis.
- **Night Cobalt Mark** (`#68a1ff`): Dark workbench actions and structural emphasis.
- **Night Deep Cobalt** (`#a9c7ff`): Dark-theme hover and emphasized code.

### Secondary
- **Banner Indigo** (`#4e52b9`): The 8px structural band at the top of stage slides.
- **Night Cobalt Wash** (`#182c4e`): Dark-theme hover and selected surfaces.

### Tertiary
- **Live Signal Amber** (`#db8a19`) and **Night Live Amber** (`#f0a439`): The live-state marker only.

### Neutral
- **Workbench Paper** (`#f4f6f8`), **Clean Sheet** (`#ffffff`), **Cobalt Wash** (`#dce9ff`), and **Muted Stock** (`#e8edf3`): Light workbench ground, raised, hover, and muted surfaces.
- **Bench Ink** (`#101820`), **Graphite** (`#475461`), and **Drafting Rule** (`#c8d0d8`): Light workbench text, secondary text, and rules.
- **Late-Night Stage** (`#0b1026`), **Chalk Lettering** (`#ecf1ff`), **Stage Haze** (`#c5d1ff`), and **Stage Line** (`#5864b7`): Persistent stage ground, text, focus, and rules.
- **Night Workbench** (`#10161d`), **Night Sheet** (`#161e27`), **Night Stock** (`#1d2937`), **Night Ink** (`#f1f5f9`), **Night Graphite** (`#aab7c4`), and **Night Rule** (`#354352`): Dark workbench surfaces, text, and dividers.
- **Control Stroke** (`#687889`) and **Night Control Stroke** (`#71859c`): Visible control borders.
- Error feedback reuses **Cobalt Wash** (`#dce9ff`) with **Deep Cobalt** (`#003a9e`) in light mode, and **Night Cobalt Wash** (`#182c4e`) with **Night Deep Cobalt** (`#a9c7ff`) in dark mode; the error state remains explicit in text.

### Named Rules
**The Signal Rule.** Use amber only for a live signal, and pair the color with readable state text; use cobalt for structure and focus.

## Typography

**Display Font:** IBM Plex Sans (with Segoe UI, sans-serif)

**Body Font:** IBM Plex Sans (with Segoe UI, sans-serif)
**Label/Mono Font:** IBM Plex Mono (with Cascadia Code, monospace)

Self-hosted IBM Plex Sans variable 5.3.0 (weights 100–700) carries clear, compact headlines and readable explanation; self-hosted IBM Plex Mono 5.3.0 marks code, status, numeric output, labels, and table headers. Both decks use the same font families.

### Hierarchy
- **Display** (700, 78px, 1.02): `.display` emphasis; `-.025em` tracking, up to 1060px wide.
- **Headline** (700, 52px, 1.12): Standard slide `h1`; `-.02em` tracking.
- **Title** (700, 30px, 1.25): Standard `h2`.
- **Lede** (400, 29px, 1.45): Lead sentence; full opacity on `p.lede`.
- **Body** (400, 24px, 1.45): Workbench explanation; `.lede` is 29px with 1.45 line-height.
- **Table** (400, 23px): Shared table text; table headings are bold.
- **Comparison** (400, 21px): Dense API-contract cells and emphasized values.
- **Caption** (400, 19px): Supporting slide context.
- **Code** (400, 20px, 1.48): Shared code blocks; inline `p.accent code` is also 20px. Compact API identifiers use 17px.
- **Comparison emphasis** (700, 26px, 1.45): First-row model comparison values.
- **Label** (400, 16px, 1.3): Monospaced shared status and interface labels; code and measurements use tabular numerals where present. Explicitly compact metadata may remain 13–14px where the live demo requires it.

Live-demo content intentionally uses a separate, denser fit scale. Decisions demo body text is 18px, with run status and generic microcopy at 16px; its compact catalog and image-demo microcopy reaches 12–13px, with small run metadata around 10–12px and code/output around 13–15px. The harness demo body and action labels/buttons are 17px and 16px respectively; harness metadata remains 13px. These are demo-specific fit constraints, not the briefing's general reading-size baseline. Decisions controls use 10×15px padding; harness controls use 8×13px. Headline and display weights do not exceed 700.

### Named Rules
**The Reading Scale Rule.** Keep the 24px/1.45 workbench body as the briefing baseline; keep deck-specific live-demo density and sub-16px text identified as fit debt, not as a new baseline.

## Layout

Slides use a 16:9 canvas. The standard workbench layout has 54px vertical and 68px horizontal padding; the demo-slide fit uses 38px and 50px. Shared spacing steps are 8, 16, 24, 32, 40, and 48px, with `.mt-2` through `.mt-5` mapped to those existing steps. The shared `.split` pattern is two equal columns with a 52px gap; live mini-apps may use their own measured columns and scrollable regions to fit their real controls and results.

### Named Rules
**The Two-Screen Rule.** Check light and dark workbench slides at 1920×1080 and 1280×720; keep content inside the canvas without overflow.

**The Workbench and Stage Rule.** Use workbench surfaces for explanations and demos; stage slides keep the same navy ground in either theme, with an 8px indigo top band.

## Elevation & Depth

This is a flat system: no box shadows, gradients, or blur. Workbench depth comes from raised, muted, and hover surface colors plus thin rules; stage depth comes from contrast, not lighting effects. No decorative grid or grain textures are used, preserving clarity on a projector.

### Named Rules
**The Flat Bench Rule.** Do not add shadows, gradients, or blur; separate content with tonal surfaces and 1px rules.

## Shapes

Controls use an 8px radius and panels use 12px. Borders are thin and functional; comparison and content panels are defined by a rule or surface change rather than a floating-card silhouette. Some dense live-demo controls use smaller local radii as fit details, not as a new shared scale.

### Named Rules
**The Shared Class Rule.** Use the shared semantic class patterns for repeated forms; do not create a new shape language in slide-local styling.

## Components

Shared CSS establishes the static briefing and reusable HTML patterns; Vue is reserved for live demos. Controls keep native semantics, visible focus, and state conveyed in text as well as color.

### Buttons
- **Shape:** 8px radius.
- **Primary:** Cobalt background and contrasting button text; live demo buttons use 10px 15px padding and 700 weight.
- **Deck-specific fit:** Decisions demo controls use 18px labels and 10×15px padding; harness controls use 16px labels and 8×13px padding. Preserve these intentional fit differences unless the slide content is re-laid out.
- **Secondary:** Raised workbench surface with a visible control border; hover uses the surface-hover color.
- **Hover / Focus:** Primary hover moves to deep cobalt. Focus is a 3px solid cobalt outline, offset 3px; stage focus uses Stage Haze.

### Chips
- **Style:** The existing `.badge` is a compact outlined marker: 1px cobalt border, 5px 10px padding, and 5px radius.
- **State:** Live state is not conveyed by color alone; pair the amber marker with text.

### Cards / Containers
- **Corner Style:** 12px for shared panels.
- **Background:** Raised or muted workbench surfaces; stage content stays on the navy stage.
- **Shadow Strategy:** None; see Elevation & Depth.
- **Border:** Use a 1px drafting rule when separation is needed.
- **Internal Padding:** Use the shared 8px spacing rhythm; `.flow-node` uses 26px as an established diagram-specific value.

### Inputs / Fields
- **Style:** Native text areas use a 1px control stroke, raised surface, 8px radius, and 14px padding.
- **Focus:** 3px solid cobalt outline offset 3px; the caret uses the current accent.
- **Error / Disabled:** Error feedback uses cobalt-tonal washes and foregrounds (`#dce9ff`/`#003a9e` light, `#182c4e`/`#a9c7ff` dark) and remains labeled in text; disabled demo controls reduce opacity and expose disabled state.

### Navigation
- **View switch:** A grouped set of buttons with a shared border, square joins, and rounded outer corners. `aria-pressed` marks the selected view; focus raises the active button above adjacent borders.

### Matrix
- **Style:** Comparison tables use thin rules and restrained tonal columns; the model-comparison pattern distinguishes the second and third columns with raised and muted surfaces.
- **Emphasis:** A 2px cobalt top rule marks the leading comparison row.
- **Diagram geometry:** Flow arrows may use a 2px border-right arrowhead; this is intentional directional geometry, not a card edge or elevation treatment.

### Live Signal
- **Style:** An 8px amber dot sits beside a monospaced text label; the live state may pulse for 1.8s.
- **State:** `data-live-state="paused"` switches the marker to cobalt; stale state lowers marker opacity. Respect reduced-motion preferences.

### Named Rules
**The Matrix Rule.** Use surface contrast and rules to compare columns; reserve the 2px cobalt edge for the leading row.

## Do's and Don'ts

### Named Rules
**The Sources-in-Notes Rule.** Put dated source citations and their supporting detail in presenter notes; navigational catalog and demo links may remain on slides.

### Do:
- **Do** keep one point on each slide and let demos do the talking.
- **Do** use shared semantic classes and plain HTML for static presentation content; use Vue only for live demos.
- **Do** use `:style` only for data-driven meter values; do not add `style=` attributes.
- **Do** retain visible 3px focus outlines with a 3px offset, using Stage Haze on the stage.
- **Do** verify light and dark workbench modes at 1920×1080 and 1280×720 with no overflow.
- **Do** pair live amber with state text; reserve cobalt for structure and focus.

### Don't:
- **Don't** create slide-local style rules or inline styles beyond data-driven `:style` meter values.
- **Don't** add shadows, gradients, blur, or decorative grid/grain textures.
- **Don't** shrink the general briefing typography to match dense live-demo content.
- **Don't** rely on color alone to communicate live, paused, stale, selected, or error state.
- **Don't** move citations and source links onto the slide canvas.
