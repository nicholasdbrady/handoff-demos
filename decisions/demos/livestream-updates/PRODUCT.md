# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Product Purpose

The Decisions demo supports The Handoff developer livestream with educational
slides and runnable demonstrations. Reuse the existing Handoff design system
to reduce manual presentation work.

## Operating Context

The existing application is a Slidev presentation with Vue live-demo components.
The presenter and audience review one slide at a time. Static review runs on
loopback without cloud calls or code execution.

## Capabilities and Constraints

- Explain decision-model concepts, Foundry API routes, and agent user-delegation
  boundaries with source-backed claims.
- Preserve the distinction between synthetic examples and verified live results.
- Optional live demonstrations require their own configuration and approval.
- Preserve uncommitted review work and change slide copy only with approval.

## Brand Commitments

Use the authoritative first-party Foundry product voice confirmed for this
livestream. Preserve the shared Handoff identity defined in the repository-root
`DESIGN.md`; this app-specific brief does not define a separate visual system.

## Evidence on Hand

`slides.md` contains the deck and presenter source notes. The local README and
tests describe runnable demonstrations and their boundaries. Root `DESIGN.md`
and `shared/handoff-theme.css` define the implemented presentation system.

## Open Decisions

This minimal record uses the existing confirmed brief and repository evidence.
No new audience, marketing claim, product commitment, or persistent build-path
default is inferred.
