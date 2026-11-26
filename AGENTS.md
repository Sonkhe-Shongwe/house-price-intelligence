# House Price Intelligence: repository working instructions

This repository builds a buyer-facing historical comparable-sales investigation and shortlist application. **This is not the PilotODIN Windows application.**

## Restore context before editing

1. Read [the documentation index](docs/DOCUMENTATION_INDEX.md), [current checkpoint](docs/CHECKPOINT.md), [P0-P8 roadmap](docs/P_PHASE_ROADMAP.md), [decisions](docs/DECISIONS.md) and the relevant engineering/phase documents.
2. Use [Master Continuation Prompt](docs/MASTER_CONTINUATION_PROMPT.md) for cross-session operating method. Follow newer user directions and verified source evidence when they conflict with older descriptions.
3. Verify current branch/HEAD, local changes and latest meaningful CI results. A GitHub copy does not expose an uninspected Windows working tree.
4. Distinguish delivery P0-P8 from audit research phases 0-2.

## Lean delivery policy

Follow the [active Lean Engineering and Delivery Directive](docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md), including its approved 23 November eight-step lifecycle and Definition of Done. P4/P5/P6 fictional-only capabilities have already been implemented in owner-authorised connected slices while P3 acceptance remains open; this does not waive their distinct phase exit gates. Prefer one authoritative implementation and small integrated buyer workflows over repeated standalone candidates. Use focused, fast, automated checks; keep valuable regression tests and add only tests for meaningful risks. Choose frameworks and dependencies by demonstrated simplification, not fashion. Do not convert documentation changes into artificial P-stage progress.

## Active frontend quality workstream (26 November 2026)

Apply the [Professional Frontend Excellence directive](docs/engineering/PROFESSIONAL_FRONTEND_EXCELLENCE_DIRECTIVE.md) within the existing eight-step lifecycle. FE1–FE7 are unweighted execution tasks under P5/P3/P6 and P7 verification, not new delivery phases. Start with FE1 iconography; use actual source/CI and rendered evidence. Defer real basemap qualification until frontend review or justified separate research. No new data, spending, access or release authority. Read the checkpoint for current status.

## Cloud-first development station (owner-approved 23 November 2026)

Apply the [cloud-first development operations](docs/engineering/CLOUD_FIRST_WORKFLOW.md) alongside the unchanged eight-step directive. Use **one GitHub repository, the permanent `development` working branch, stable `main`, and GitHub Actions for routine verifiable tests**. Source changes are authored on `development` through authorised GitHub/cloud tools; Actions executes builds and checks rather than automatically writing code. Create a PR from `development` to `main` at an accepted milestone, not one new branch/PR per small fix. Never squash-merge or force-rewrite the permanent development history by default. Pull to Windows only for essential platform testing or owner UX acceptance. Never create another active app workspace or serial review ZIP as a substitute for integration. Separate observed manual tests, unmerged patches and committed CI evidence. Standing authority covers routine scoped development commits; main merge, deployment, repository rules and live-data dispatch retain their separate approval requirements.

## Standing engineering autonomy (25 November 2026)

Routine engineering within the approved scope is delegated: independently select and implement the next integrated task, commit to development, run and diagnose CI, correct regressions and continue toward a meaningful milestone in the available execution session. No separate owner approval for ordinary scoped edits or synthetic verification. Ask only for indispensable owner action or a genuine cost, credential/access, data-rights, live-data, destructive-operation, release or main-integration boundary. Preserve the eight-step directive, exact-head evidence and phase gates. Do not claim unattended execution after the session ends. Prefer working software to new process documents.

## Engineering boundaries

- Use connected Neon administration for scoped development work and read-only inspection. Reverify actual project/branch, never use production by default, retain direct application TLS/role/recovery and real-data gates, and keep secrets/endpoint identifiers out of public commits. See [cloud integration](docs/engineering/NEON_CLOUD_INTEGRATION_V1.md).

- Prioritise traceable data, correct joins, source/time limitations, reproducible tests, clear comparable evidence and a complete buyer workflow.
- Do not conflate recorded sales with a property listing or user-reported asking price. Never label exploratory 2 km spatial fallback prices as validated valuations.
- Keep publisher data, user data, property-level raw extracts and credentials out of public commits or artifacts. Publication/display rights have not been approved.
- The integrated local **fictional-only** backend/browser/SQLite/shortlist is verified on `development`, but it is **not an approved production** database, real-property API, final buyer UI, deployment or price-prediction model. Consult the [current checkpoint](docs/CHECKPOINT.md).
- Preserve dated audit reports; update current handoffs and decisions only with new evidence. Use `python tools/check_docs.py` for internal Markdown links and P-stage arithmetic. For map work, consult [mapping research](docs/design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md): the original synthetic coordinates overlap; current versioned fictional MapLibre display is documented in [synthetic map contract](docs/engineering/SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md). Real tiles, geocoder, source and public display remain unapproved.
- Standing authority permits routine commits to development within approved scope; manually dispatched live data audits, scheduled cloud jobs and deployment still require the relevant approval.
- Never force-push or delete/rewrite uncommitted work or retained evidence.

For current work, follow the latest acceptance gate and its tests. If no local checkout is visible, report that limitation rather than claiming a clean working tree.
