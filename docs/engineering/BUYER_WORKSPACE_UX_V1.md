# Buyer Workspace and UX Consolidation V1

**Owner-authorised on 24 November 2026.** Direct development changes; no main merge, deployment or real records. P3.1–P3.7 are accepted as the provisional synthetic contract only. Production architecture, P3.8–P3.11 and real source rights remain unresolved.

## Requirements and architecture
UX1 responsive navigation and workspace; UX2 read-only bounded history; UX3 discovery and reopening; UX4 evidence dossier; UX5 dedicated comparison; UX6 keyboard/reflow and explicit caveats; UX7 canonical integrated tests. Keep one React application and existing Python/SQLite services. No new schema, dependencies or browser-side storage. The root opens Workspace; /buyer-workflow opens Investigate. Other views are in-app navigation. The comparison component stays mounted so unsaved drafts survive navigation; a beforeunload warning covers drafts, pending writes and recovery. Map renderer unmounts off Investigate. Existing explicit technical UUID controls remain.

## History contract
GET /v1/investigations/history (synthetic-history-v1) lists up to 30 most recent results within the current trusted build in deterministic created-time/ID order. A 31st row signals truncation. Each row is reopened through existing frozen verification; failures reject the entire index. Minimal summary includes ID, date, buyer label/PIN/asking price, evidence status/count and creation time; no sale payload, coordinates or user notes. No query parameters or external access; local filter covers latest 30 only. Older known IDs still reopen. Read-only and does not rematch. No change to POST /v1/investigations or its GET-by-ID contract.

## Risks and verification
Preserve frozen response, exact cents, source provenance, map identity, shortlist recovery and unknown-property abstention. Navigation must never remount the shortlist or discard notes. UI states distinguish history unavailable and no saved investigations. Keyboard controls and mobile reflow tested, not full WCAG conformance. Existing regression tests updated only for intentional navigation. New HTTP history tests verify bounded list, method/origin checks and tampered response rejection; real browser journey tests history, weak evidence, note drafts across views, restart and responsive navigation. CI must pass exact head before owner UX acceptance. Visual review pending. Official P3 10%, weighted MVP 22.8% remain unchanged pending formal phase exit; provisional synthetic approval is not whole-P3 acceptance.

## Handoff
See [checkpoint](../CHECKPOINT.md), [P3 contract](P3_APPLICATION_CONTRACT.md), [geographic contract](SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md). No new source data or release rights.
