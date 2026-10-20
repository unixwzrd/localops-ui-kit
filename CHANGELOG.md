# Changelog

## 0.2.0 — 2026-10-20

Public-preview preparation. No component API changes from the 0.1.5 candidate: browser API remains 0.1.5, Python API remains 0.1.4 and manifest schema remains 1. Package versions and API versions serve different purposes.

- Added a grouped widget reference and a browser-only showcase using synthetic, in-memory adapters.
- Added project banner artwork for the README/showcase and documented direct pip installation from GitHub, optional renderer extras and reproducible commit pins.
- Added a Python-only, allowlisted static-site assembly command and manual GitHub Pages deployment workflow. No Node runtime, bundler, CDN or application backend is needed.
- Excluded local consumer journals, environment files, generated evidence and site output from future commits. Public compatibility information describes contracts, not private consumer qualification records.
- Included the previously local ContentPanel addition and its populated-search Escape fix. Plain non-composing Escape closes the innermost panel, preserving the query and restoring focus; modified shortcuts and composition are not intercepted.

This is a pre-1.0 preview, not a claim of production readiness, consumer adoption, hardware IME qualification or actual Safari-app acceptance. Review the [capability matrix](docs/capability-matrix.md) before assuming WebUI/TUI/CLI parity.

## 0.1.5

Corrected ContentPanel Escape handling for populated native search inputs in Chromium. Public component signatures are unchanged from 0.1.4.

## 0.1.4

Added ContentPanel for consumer-trusted DOM and literal text, responsive expansion, modal focus recovery and a strict Python ContentPanelState. The populated-search Escape limitation was corrected in 0.1.5.

## 0.1.1–0.1.3

Added ResultReader, explicit shell navigation closing and CodeEditor with strict Python direct-component contracts. These direct components do not add dedicated terminal or manifest nodes.

## 0.1.0

Initial Python-first foundation: native browser modules, semantic models, optional Textual/Rich renderers and the Python rendered-layout test kit.
