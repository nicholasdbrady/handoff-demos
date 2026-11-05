---
name: cookbook-review
description: Review a small Microsoft Foundry recipe notebook for correctness, clarity, and runnability before returning it to the user.
---

# Cookbook review

Demo-sized adaptation of the Forgebook Recipe Factory review contract.
Review the notebook as a runnable lesson, not a feature tour.

Check thesis, opinionated defaults, when/what/how, code discipline,
before/after evidence, runnability, scope, developer voice, failure modes,
takeaway artifact, and learning objectives. Return a finding and a verdict for
each of the eleven axes. Use the user's weights and the 105-point total.

Read the notebook from disk. Validate notebook JSON, confirm nbformat 4,
and compile Python code cells without executing cloud calls. Distinguish
syntax checks from live execution. Ask a read-only subagent for an independent
review if available. Fix critical local defects and rerun local checks.

Never approve fabricated outputs or untested Azure calls. Report any missing
package or permission explicitly. Do not install dependencies, provision
resources, commit, push, or open pull requests. Save the review next to the
notebook, then return both artifacts.
