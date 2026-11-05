# Pack for the Plot Twist

Original, AI-generated photorealistic fixtures for this demo. No third-party
game, photograph, puzzle, or character assets are copied. The photographs are
synthetic and are labeled as such in the deck.

| Fixture | Visible evidence |
| --- | --- |
| `sunshine.png` | Shirt, shorts, straw hat, flip-flops, and a sunscreen-style bottle |
| `rain.png` | Hooded coat, umbrella, closed boots, and folded trousers |
| `obscured.png` | Opaque covers hide both suitcase compartments |

Generated on 2026-10-27 through `/generate-image`, using the fixed Microsoft
Foundry `gpt-image-2` deployment and Entra authentication. One sequential
three-prompt batch, medium quality, requested 1536x1024 PNG, no augmentation.
Exact final prompts are preserved in `generation-prompts.jsonl`, in fixture
order: sunshine, rain, obscured. Generated output can differ from the prompt:
for example, sunglasses were requested but are not visible in the retained
sunshine photo. Questions must evaluate actual pixels, not the intended list.

The model receives PNG pixels, not filenames, expected labels, or our fixture
descriptions. The earlier vector fixtures were replaced after real model
calls failed to recognize some drawn equipment; these photos must also be
tested rather than assumed reliable.

These are synthetic teaching inputs, not an accuracy dataset. A photograph
cannot establish whether a coat is truly waterproof, what hidden items exist,
or whether luggage meets safety requirements. The trip-fit rubric is a demo
judgment, not travel or safety advice. Exact counts and arithmetic belong in
code. Ambiguity and refusal route to review.
