# Kimi K3.1 Pro: large-code, image, and multi-hop benchmark

This harder example accompanies the preserved three.js sculpture comparison.
It is a **bespoke functional benchmark**, not a standard leaderboard result.
Three independent seeded trials each send **373,132 service-reported input
tokens**: a complete public Azure AI Projects model source file, its changelog
and license, distributed planted records, and a routing-policy image.

The model must read the image, choose a route, follow three links across the
large corpus, exclude stale epochs, compute a checksum, and find real SDK type
facts. It returns 11 fields, automatically graded for exact values and types.
Every route has a valid text chain, so the corpus cannot reveal which route
the image selects. The source code is real; planted routing records are
explicitly fictional.

## Results captured November 9, 2026

All three attempted trials are included in the denominator. No retries, tools,
code execution, answer repair, baseline model, or replay fallback were used.

| Trial | Exact answers | Input tokens | Output tokens | Reasoning within output | Total tokens | Time | Uncached cost estimate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 11/11 | 373,132 | 740 | 647 | 373,872 | 37.273 s | $0.866714 |
| 2 | 11/11 | 373,132 | 547 | 454 | 373,679 | 26.563 s | $0.864494 |
| 3 | 11/11 | 373,132 | 775 | 682 | 373,907 | 24.967 s | $0.867116 |

**Trial pass rate: 3/3 (100%). Item pass rate: 33/33.**
Median latency: **26.563 seconds**. Total conservative uncached estimate:
**$2.598324**. Reasoning effort was `high`; the completion allowance was 4,096
tokens. Reasoning tokens are included in output, not added to total.

Each input contains 1,595,059 characters. The independent `cl100k_base` estimate
is 378,911 tokens, but that is **not Kimi's tokenizer**. The reported size comes
from the live response's token usage. Fixtures occur near the early, middle, and late sections of the corpus;
consult each provenance file for exact character offsets.
All code is present once; there is no repeated padding to inflate the size.

A three-trial success is not evidence of universal reliability, a model
ranking, or one-million-token performance. The common code corpus is shared,
while the seeds, tickets, routing image, epochs, values, and expected joins
change. This tests long-input use, visual policy reading, and deterministic
multi-hop answers, not code synthesis or execution.

## Run from handoff-demos

Cwd: `weekly-brief/2026-11-06`. Prerequisites: Python 3.12+, uv, a public
`Azure/azure-sdk-for-python` clone, Azure CLI login, and Entra inference access
to a Kimi K3.1 Pro deployment with enough quota for at least 374K input tokens
per request. Allow three paid calls. The benchmark reuses the preserved
sculpture demo's Foundry client; both commits must be integrated.

User-provided `.env` in the weekly folder, benchmark folder, or exported shell:

```dotenv
KIMI_ENDPOINT=https://YOUR-RESOURCE.cognitiveservices.azure.com/openai/v1/
KIMI_DEPLOYMENT=kimi-k3-1-pro
KIMI_AUTH=cli
```

Omit `KIMI_AUTH=cli` to use `DefaultAzureCredential`. No keys are needed.
Environment is server-side only: there are no `VITE_` keys or credentials in
the visual. If the benchmark's `.env` is absent, the shared client can also
read the sculpture demo's local `.env`. Exported values take precedence.

Rebuild from the captured public commit:

```powershell
$commit = (Get-Content public\demos\kimi-k3-1-pro-benchmark\provenance-1.json -Raw | ConvertFrom-Json).source_commit
uv run demos\kimi-k3-1-pro-benchmark\build_corpus.py --source D:\repos\azure-sdk-for-python --commit $commit --trials 3
```

The command reads the exact source commit from the captured provenance.
The builder reads tracked committed
source, not local drafts. Omitting `--commit` selects the clone's current HEAD.
It creates local gitignored corpora and oracles; the large corpus is not
committed.

Render the SVG inputs to PNG using ImageMagick, from the weekly folder:

```powershell
magick public/demos/kimi-k3-1-pro-benchmark/input-1.svg public/demos/kimi-k3-1-pro-benchmark/input-1.png
magick public/demos/kimi-k3-1-pro-benchmark/input-2.svg public/demos/kimi-k3-1-pro-benchmark/input-2.png
magick public/demos/kimi-k3-1-pro-benchmark/input-3.svg public/demos/kimi-k3-1-pro-benchmark/input-3.png
uv run demos/kimi-k3-1-pro-benchmark/test_benchmark.py
```

The PNGs used in the captured calls are committed, so ImageMagick is needed
only when rebuilding inputs. Each SVG carries an explicit fictional-data
label. Its labels are large; rasterizer font fallback can differ by machine.
The slide visual itself embeds licensed IBM Plex Sans and needs no installed
font.

```powershell
uv run demos/kimi-k3-1-pro-benchmark/run.py --json --trial 1 --effort high --max-tokens 4096 --record public/demos/kimi-k3-1-pro-benchmark/trial-1.json
uv run demos/kimi-k3-1-pro-benchmark/run.py --json --trial 2 --effort high --max-tokens 4096 --record public/demos/kimi-k3-1-pro-benchmark/trial-2.json
uv run demos/kimi-k3-1-pro-benchmark/run.py --json --trial 3 --effort high --max-tokens 4096 --record public/demos/kimi-k3-1-pro-benchmark/trial-3.json
uv run demos/kimi-k3-1-pro-benchmark/build_report.py
```

One JSON object is printed for each real call. The process exits nonzero for
API error, incomplete output, any grading failure, or fewer than 200K measured
input tokens. The default timeout is 180 seconds; `--timeout 120` is available
for a live-show guard. There is no automatic retry. uv uses inline dependency
metadata. Approved feed fallback:
`https://packagefeedproxy.microsoft.io/pypi/simple`.

## Show the captured benchmark without Azure access

Serve the weekly `public` directory:

```powershell
uv run python -m http.server 8794 --bind 127.0.0.1 --directory public
```

Open `/demos/kimi-k3-1-pro-benchmark/benchmark.html`. It is a self-contained
authored visual with inline data, an embedded input image, and embedded
licensed fonts. It makes no fetch or inference calls. The deck can put this
document into a unique-origin `sandbox="allow-scripts"` iframe without
`allow-same-origin`. The document's CSP blocks network calls and forms.

The overview uses navy/cobalt, IBM Plex, and labels at least 24px. Expand the
prompt/grading and usage/model-status sections for the full evidence.
The image-policy table is an authored transcription for projector legibility,
not a model response. The unmodified actual input image is in its own
expandable section. The essential overview fits 1280 x 720 and 1920 x 1080;
mobile and expanded evidence scroll vertically. `overview.png` and
`browser-validation.json` preserve the observed browser checks.
The single font family is intentional; 52px headings, 30px result text,
24px labels, and bold weights provide the hierarchy without shrinking labels.

## Grading and reproducibility

The exact output keys are:
`route`, `ticket`, `epoch`, `change_id`, `shard`, `release`, `checksum`,
`snapshot_field`, `snapshot_optional`, `soundscape_type`, and
`first_release_heading`. JSON types matter: `true` does not equal integer `1`;
extra keys fail the trial. The checksum is `(17*x + 31*y + z) % 997`.

The builder parses the full committed `_models.py` with Python AST and the
changelog with a level-two-heading parser. It derives the source facts instead
of accepting model assertions. The fictional fixture oracle is deterministic
from each seed. Three valid routes and stale versions are deliberately
included, with their joins separated across the source corpus.

The recorded results include the raw answer, expected answer, individual
field flags, actual token usage, latency, uncached cost inputs, prompt, seed,
source URLs, source SHA, fixture offsets, and corpus hashes. Failed calls are
not omitted by the report builder. The cost calculation is an estimate, not a
billing receipt; caching and agreement pricing may reduce or change the bill.

## Model and resource evidence

Primary sources retrieved **Nov 9, 2026**:

- [Nov 5 Microsoft announcement](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292):
  text and image understanding, up to one million context tokens, $2.30/M input,
  $0.23/M cached input, and $11.50/M output.
- [Current catalog](https://ai.azure.com/catalog/models/Kimi-K3.1-Pro):
  **Generally available (GA)**; text/image input; 1048.576k context.
- [Learn retirement schedule](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule#foundry-models-sold-by-azure):
  `Kimi-K3.1-Pro | 2026-11-04 | GA | 2027-11-04`.

The supplied weekly draft said preview. We have not established a historical
lifecycle label by the **Nov 6, 12:01 PST** reporting cutoff. Preserve the dates
instead of treating the current GA label as historical proof.
The deployment model is `Kimi-K3.1-Pro`; the service response calls itself
`Kimi-K3.1`. Both are retained.

No new benchmark Azure resources were created. The earlier tagged
`handoff-kimi-20261109` Foundry resource in `rg-handoff-kimi-20261109`, East US,
was reused. Its `kimi-k3-1-pro` Global Standard deployment was increased from
100 to **1,000 capacity units (1M TPM)** to admit these long requests.
Only this session-created resource was changed. No marketplace terms,
provisioned commitment, extra RBAC, or existing unrelated resource was touched.

Leave it available until the show ends. Cleanup remains the earlier demo's
scoped resource-group cleanup, after the presenter is finished.
