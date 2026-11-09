# Source and asset notices

The Decisions and Copilot harness demo code was imported from the private
`nbrady_microsoft/agent-factory` project. The source root did not contain a
code license. The rights holder explicitly authorized public redistribution of
these imported demos under MIT and specified **Nick Brady** as the copyright
holder on 4 November 2026.

This authorization covers the imported demo source, not third-party dependencies
or artwork. The repository MIT license must not be interpreted as relicensing
those materials.

## Import provenance

- Decisions: frozen export prepared from the `decisions-api-and-agent-obo-demos`
  source at `1c92a83` plus its local authentication fixes. Export commit:
  `1a473293666b428fce89f178e6e0241c01188501`; original `demos/` tree:
  `5c1b2dea13973d26deaada990e374d06b285689e`.
  The imported copy has local environment-loading and portable onboarding fixes.
- Copilot harness: allowlisted files from `demos/copilot-harness-livestream`
  in the `copilot-harness-livestream-deck` working tree. Adapted for standalone
  use without the source repository's `lib`, hosted runner, or Fusion backend.
  Original recordings were excluded and replaced with labeled synthetic fixtures.
- Source Git histories, credentials, deployment state, and runtime records were
  not imported.

## Artwork and dependencies

- Decisions catalog photographs retain their
  [Unsplash source and license notice](decisions/demos/livestream-updates/public/catalog/CREDITS.md).
- Synthetic [mug fixtures](decisions/demos/livestream-updates/public/decision-images/README.md)
  and [packing fixtures](decisions/demos/livestream-updates/public/packing/README.md)
  retain generation provenance. They are teaching illustrations, not real
  customer evidence or evaluation datasets.
- The slide-3 harness Orbit diagram is original artwork made for this deck by
  the repository owner. The README SVG is
  original code-native artwork for this repository. Campaign avatar/title art
  and corporate logos were not imported.
- Dependencies retain their own licenses. Package installation does not grant
  rights to Microsoft brands or imply endorsement.
- Both decks self-host IBM Plex Sans and IBM Plex Mono through Fontsource
  packages. These fonts retain their SIL Open Font License 1.1; the license
  files ship with `@fontsource-variable/ibm-plex-sans` and
  `@fontsource/ibm-plex-mono`. They are not relicensed under this repository's MIT
  license.
