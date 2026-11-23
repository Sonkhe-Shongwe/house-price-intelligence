# House Price Intelligence: repository working instructions

This repository builds a buyer-facing historical comparable-sales investigation and shortlist application. **This is not the PilotODIN Windows application.**

## Restore context before editing

1. Read [the documentation index](docs/DOCUMENTATION_INDEX.md), [current checkpoint](docs/CHECKPOINT.md), [P0-P8 roadmap](docs/P_PHASE_ROADMAP.md), [decisions](docs/DECISIONS.md) and the relevant engineering/phase documents.
2. Use [Master Continuation Prompt](docs/MASTER_CONTINUATION_PROMPT.md) for cross-session operating method. Follow newer user directions and verified source evidence when they conflict with older descriptions.
3. Verify current branch/HEAD, local changes and latest meaningful CI results. A GitHub copy does not expose an uninspected Windows working tree.
4. Distinguish delivery P0-P8 from audit research phases 0-2.

## Lean delivery policy

Follow the [active Lean Engineering and Delivery Directive](docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md), including its approved 23 November eight-step lifecycle and Definition of Done. P4/P5 may be implemented in connected slices after P3 acceptance, but have distinct acceptance gates. Prefer one authoritative implementation and small integrated buyer workflows over repeated standalone candidates. Use focused, fast, automated checks; keep valuable regression tests and add only tests for meaningful risks. Choose frameworks and dependencies by demonstrated simplification, not fashion. Do not convert documentation changes into artificial P-stage progress.

## Cloud-first development station (owner-approved 23 November 2026)

Apply the [cloud-first development operations](docs/engineering/CLOUD_FIRST_WORKFLOW.md) alongside the unchanged eight-step directive. Use **one GitHub repository, the permanent `development` working branch, stable `main`, and GitHub Actions for routine verifiable tests**. Source changes are authored on `development` through authorised GitHub/cloud tools; Actions executes builds and checks rather than automatically writing code. Create a PR from `development` to `main` at an accepted milestone, not one new branch/PR per small fix. Never squash-merge or force-rewrite the permanent development history by default. Pull to Windows only for essential platform testing or owner UX acceptance. Never create another active app workspace or serial review ZIP as a substitute for integration. Separate observed manual tests, unmerged patches and committed CI evidence. Do not commit, merge, deploy, change repository rules or dispatch live-data jobs without the relevant owner authorisation.

## Engineering boundaries

- Prioritise traceable data, correct joins, source/time limitations, reproducible tests, clear comparable evidence and a complete buyer workflow.
- Do not conflate recorded sales with a property listing or user-reported asking price. Never label exploratory 2 km spatial fallback prices as validated valuations.
- Keep publisher data, user data, property-level raw extracts and credentials out of public commits or artifacts. Publication/display rights have not been approved.
- No approved production database, backend API, browser UI, deploy or price-prediction model is implied by the existing research pipeline.
- Preserve dated audit reports; update current handoffs and decisions only with new evidence. Use `python tools/check_docs.py` for internal Markdown links and P-stage arithmetic.
- Do not automatically publish Git changes, manually dispatch live data audits, change scheduled cloud jobs or deploy without the owner's relevant approval. A specific user instruction to update GitHub permits the bounded changes requested.
- Never force-push or delete/rewrite uncommitted work or retained evidence.

For current work, follow the latest acceptance gate and its tests. If no local checkout is visible, report that limitation rather than claiming a clean working tree.
