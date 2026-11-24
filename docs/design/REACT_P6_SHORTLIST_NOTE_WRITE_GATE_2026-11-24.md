# HPI React P6 shortlist and note-write experiment

**Recorded:** 24 November 2026. **Scope:** Isolated localhost-only, fictional SQLite P6 browser milestone. This is neither a final frontend migration nor formal acceptance of P6, the UI, or real evidence rights.

## Goal and verified design boundary

A saved investigation already has a frozen, source-checked P3 response. The new React buyer workflow can create one P6 shortlist, add saved fictional investigations, and save buyer notes using the original backend shortlist service. The React browser does **not** edit recorded sale amounts, matching policy, source snapshot ids, or any geographic data.

The source-backed component is `design-prototypes/react-map-spike/src/SavedComparison.tsx`. It is rendered beneath the saved investigation in `BuyerWorkflow.tsx`, which already performs the explicit candidate -> address-resolution -> POST investigation -> GET frozen result journey.

## API flow: no newly invented back-end endpoints

- POST `/v1/shortlists` with a label <=80 chars produces a new UUID and empty shortlist.
- GET `/v1/shortlists/{id}` reopens the real Python/SQLite shortlist.
- POST `/v1/shortlists/{id}/entries` adds a saved investigation UUID. The UI verifies the investigation first via GET and rejects duplicate ids and same-PIN duplicate property selection. The **Python** service independently rejects duplicate investigations/properties, unknown saved records and exceeding three entries.
- PATCH `/v1/shortlists/{id}/entries/{investigation_id}` stores only `note_text`, limited to 800 characters; no matching result or source row is modified.
- The component reads each mutation response, adapts it through the original trusted P3/P6 TypeScript boundary, **reopens the saved shortlist with GET** and requires the two representations to agree. For all entries present before the write, it also checks that the P3 presentation and matching policy are unchanged. Unexpected data shows an error, not a successful save.
- Users may reopen by shortlist UUID during the same server session; notes are not merely browser-local or claimed persistent across app restarts.

An interrupted mutation may already have committed server-side. The UI instructs the user to refresh the saved shortlist before retrying and does not silently duplicate the request. When one note is saved successfully, other cards' unsaved local drafts stay available until their own explicit Save action; manual reopen reloads the authoritative notes from Python. A source contract mismatch invalidates confirmation and is never treated as a completed note save.

## Privilege boundary

The preview launcher `tests/source_preview_server.py` retains all previous modes and adds a **second explicit flag**:

```bash
npm ci --prefix design-prototypes/react-map-spike
npm run build --prefix design-prototypes/react-map-spike
python design-prototypes/react-map-spike/tests/source_preview_server.py --port 8797 --enable-buyer-workflow --enable-shortlist-workflow
```

Then navigate to **http://127.0.0.1:8797/buyer-workflow**.

- Without either flag: the source review remains read-only, and the previous buyer workflow is not available.
- With only `--enable-buyer-workflow`: address-search and investigation-creation POSTs are permitted, but shortlist writes remain disabled and the React shortlist section identifies itself as disabled.
- With both flags: only shortlist creation (POST `/v1/shortlists`), adding entries (POST `/v1/shortlists/{sid}/entries`), and editing an existing note (PATCH `/v1/shortlists/{sid}/entries/{iid}`) are additionally allowed. **DELETE remains disabled**, and no other route gains write permissions.
- The local WSGI wrapper preserves loopback-only binding, source-kind restrictions, Host/Origin/forwarded-header checks, fixed precompiled asset allowlist, no-store, strict CSP and no third-party map requests. Delegated requests keep the underlying Python JSON size/typing/duplicate-key validation.

This remains **single-user localhost and disposable in-memory SQLite only**. It is not an authentication system, multi-user permission model, production security approval or a durable record store.

## Browser coverage

`design-prototypes/react-map-spike/tests/test_saved_comparison.py` checks the real Chrome browser against the genuine fixture Python WSGI and SQLite:
1. Create a new empty shortlist and add the saved current investigation.
2. Add a second distinct parcel, patch a saved note, re-GET the real stored note and compare frozen sale evidence before/after.
3. Reopen the saved shortlist after reloading the browser, recovering the real stored note.
4. Refuse multiple investigations representing the same PIN.
5. Add an existing verified investigation by UUID and refuse duplicate membership.
6. Enforce the three-unique-property limit in both browser and Python.
7. Reject oversized notes and malformed investigation identifiers without mutating source evidence.
8. Block cross-origin/proxied writes, arbitrary mutations and DELETE.
9. Admit an insufficient-evidence investigation without fabricating a value.
10. Retain an unsaved draft on another property while confirming one note with Python.
11. Verify 320px/375px mobile reflow without horizontal overflow and reduced-motion treatment.
12. Capture desktop/mobile screenshot artefacts in the hosted CI run.

The existing independent six visual/WebGL tests, seven source-review browser tests and eight buyer-creation browser tests remain part of the isolated workflow. Actual pass status must be checked for the **exact branch SHA** before declaring this milestone accepted as a technical proof.

## Product decisions intentionally deferred

- Whether to adopt the new React visual direction and replace the original frontend.
- Whether the existing local-only demo WSGI can be refactored for a reviewed manifest-based production asset serving and user session model.
- Durable persistence, authentication, user privacy and multi-user separation, all **not provided** here.
- History as-of source provenance, permitted external data and real property/parcel-level geography. The shortlist remains text-evidence-only with no fake map coordinates.
- P-stage formal scoring and release authority. Overall 22.8%, P3 10% and P4-P6 0% formal baseline unchanged.

**Branch boundary:** This source lives only in `feature/react-maplibre-full-spike-validation-20261123`. Neither `development` nor `main` nor draft PR #4 is merged by implementing this proof.
