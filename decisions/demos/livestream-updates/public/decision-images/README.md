# Synthetic image fixtures

These are AI-generated illustrations, not customer photos, proof of delivery,
or a model evaluation dataset. The deck labels them synthetic.

| File | Intended visible content |
| --- | --- |
| `intact.jpeg` | A white ceramic mug with no visible damage |
| `damaged.jpeg` | A white mug with a visible body crack and chipped rim |
| `unclear.jpeg` | A dark, blurred, partly cropped mug; damage cannot be judged reliably |

Generated on 2026-10-27 using `/generate-image`, the fixed Microsoft Foundry
`gpt-image-2` deployment, Entra authentication, and one sequential batch.
Dimensions: 1536 x 1024. JPEG, quality medium, compression 85.
The three exact final prompts are in `generation-prompts.jsonl`, in the table
order. No prompt augmentation was applied. No personal data or branded
packaging was supplied.

The image-only slide sends pixels and questions. The image-plus-text slide
adds a fictional return policy and explicit purchase age. Neither can prove
purchase history, delivery, authenticity, or refund entitlement.
The same photo can be used with either policy age; changing the age does not
change its pixels.
