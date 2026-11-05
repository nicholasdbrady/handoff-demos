# Shared recipe-author task

Use the following prompt unchanged for every harness. Start a fresh session.

```text
Draft a small Microsoft Foundry Forgebook tutorial notebook that teaches one pattern: call a deployed model with the OpenAI Responses API using Microsoft Entra authentication.

Audience: a Python developer who already has a Foundry project and a model deployment. Use FOUNDRY_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME environment variables, DefaultAzureCredential, and AIProjectClient.get_openai_client(). Do not create cloud resources. Do not execute live model calls from the generated notebook.

Write notebooks/entra-responses.ipynb and review.json in your workspace. The notebook must be nbformat 4, must not start with an H1, and must have clean code cells (execution_count null, outputs []). Include audience, prerequisites, learning objectives, an outline, a dependency cell, configuration, one minimal Responses call, expected output explicitly labeled illustrative, one authentication failure and fix, and a reusable takeaway. Keep it to 6-10 cells.

Self-review the notebook against these eleven weighted axes: thesis 15, opinionated defaults 10, when/what/how 10, code cell discipline 10, before/after evidence 15, runnability 15, scope 10, dev-to-dev voice 5, failure modes 5, takeaway artifact 5, learning objectives 5. Weights total 105. Each score is 0-5; weighted score is sum(score / 5 * weight). Publish is 95-105, publish after fixes 79-94, revise and resubmit 63-78, otherwise not ready. Missing reproducible evidence, missing thesis, or a critical runnability issue blocks Publish.

Use an independent reviewer subagent if your harness supports one; otherwise state that the review is a self-review. Save scores, weighted total, verdict, blockers, and whether the notebook was executed in review.json. Validate notebook JSON and Python syntax, but do not claim the notebook ran. Finish with a brief summary, artifact paths, validation performed, and any publication blocker. Do not open a PR or publish the recipe.
```

## Fair comparison

- Same task, model deployment (`gpt-6-luna`), fresh workspace, and rubric.
- Generated notebook execution is prohibited; model inference for the author is allowed.
- The eleven-axis, 105-point rubric reflects the current factory review skill.
  The factory README still describes ten axes; do not silently reduce the rubric.
- Validation is structural and syntax-only. An illustrative output is not live evidence.
- Capability differences (built-in vs code-defined tools and subagents) remain visible.
- Generated output is a draft, not an upstream Forgebook contribution.
