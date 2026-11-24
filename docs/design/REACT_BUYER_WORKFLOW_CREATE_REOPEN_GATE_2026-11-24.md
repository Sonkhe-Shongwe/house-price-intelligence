# HPI React Buyer Workflow: explicit parcel selection, save and reopen

**Date:** 24 November 2026
**Classification:** Isolated, opt-in, fixture-only experimental workflow. Not an approved product migration, public site, real property database, login system or phase exit.

## What changed

The React prototype has a separate **/buyer-workflow** route, alongside the original invented-geometry design laboratory at / and the immutable GET-only /source-review.

The browser now can:

1. **Search fictional addresses** through the original Python POST /v1/addresses/search. Multiple parcel choices for the same address remain separate.
2. **Select an explicit parcel** and verify its PIN, display address, parcel-only identity and unverified building status through GET /v1/addresses/{id}. The user cannot save based on an unresolved search result.
3. **Review inputs** for area, user-reported asking price and an historical analysis date, then deliberately press Save Investigation. The React app posts only those fields and the exact selected address_id/PIN to POST /v1/investigations. Python alone resolves identity and matches earlier sales.
4. **Reopen the frozen result** by immediately calling GET /v1/investigations/{uuid}, validating the v0.3 evidence contract and comparing the newly returned source data with the saved result before showing it. Users can paste the saved UUID later in the same local server session to reopen without rematching.
5. **Inspect evidence**, including exact USD sale-price strings, previous-sale explanations, the evidence tier, source snapshots, and the explicit absence of a current valuation.
6. **See the unavailable-geography state** instead of the fictional map pins from the design study. The server has no trusted map feature API and nothing in this workflow calculates distances.

Only the fixture in-memory SQLite database is written. Its contents and saved UUIDs disappear when the local preview server shuts down. No account-private storage or real transactions are involved.

## Security boundary

The isolated source_preview_server.py retains the original **read-only** behaviour unless started with the explicit --enable-buyer-workflow flag. In that mode:

- The only newly enabled write paths are POST /v1/addresses/search and POST /v1/investigations. The former performs a lookup without writes, and the latter saves a fictional investigation.
- All other POST, PATCH and DELETE methods remain disabled at the preview boundary, including shortlist creation/editing and deletion.
- The trusted backend still performs JSON content-type, size, duplicate-key, Host, Origin, proxy-header, foreign-identity and source-kind validation. The wrapper itself retains loopback-only checks and rejects query strings and unknown paths.
- The compiled Vite JS/CSS is served through a finite startup-time asset allowlist. A strict default-deny CSP prohibits external sources, inline script exceptions and network tiles. No arbitrary filesystem server or wildcard CORS is introduced.
- The browser uses same-origin requests and no-store caching, invalidates outstanding address selection requests when the search changes, and clears previous results during failed reopen/contract validation. Mutation occurs only on user submission.
- Every saved investigation returned from Python is validated against the typed evidenceBridge adapter. Unexpected valuation, unsupported fixture source, malformed money, bad identity or missing provenance cannot be silently displayed.

The server has no user authentication, accounts, multi-user isolation or public network interface. This is not a production security review or authorisation to serve it remotely.

## Clean local run on the isolated feature branch

From the repository root:

    npm ci --prefix design-prototypes/react-map-spike
    npm run build --prefix design-prototypes/react-map-spike
    python design-prototypes/react-map-spike/tests/source_preview_server.py --port 8797 --enable-buyer-workflow

Open **http://127.0.0.1:8797/buyer-workflow**.

Useful fictional queries: **101 Fictional Way** (one candidate) and **105 Fictional Court** (two distinct synthetic parcel options). The existing /source-review remains available as a separate read-only screen.

To run without any permission to create investigations, restart the server without the --enable-buyer-workflow switch.

## Browser acceptance

A new test suite called test_buyer_workflow.py exercises eight actual Chromium scenarios in the isolated GitHub Actions workflow:

- Distinct option A and B at one address, with create disabled until explicit verified choice.
- Preserved buyer-reported cents versus source sale cents; original matching explanation and snapshot provenance.
- Changing the search clears a previous selection and blocks stale create.
- Create followed by GET reopen, and later reopening the frozen result by UUID without new matching.
- Invalid or unknown UUID errors clear stale evidence.
- Only the permitted fixture POST paths work; arbitrary writes, cross-origin, proxy headers, invalid JSON and unapproved static files are denied.
- Responsive 375px/320px browser layouts and reduced-motion treatment.
- Four actual Chrome visual-review screenshots (empty, ambiguous candidate choice, saved evidence and mobile).

These run alongside the six original MapLibre/SVG visual tests, seven read-only source integration tests, and the actual WSGI-to-TypeScript integrity assertions. Check the newest **exact-SHA GitHub Actions result** before treating any regression result as passed.

## Remaining decision gates

- This implementation lives **only on the isolated feature branch**. Canonical development, stable main, PR #4, the existing browser UI, backend/SQLite schemas and 22.8% formal acceptance baseline are not changed.
- It does not yet add the editable shortlist/notes workflow to React. That should be a separate, source-verified transaction milestone after this create/reopen proof is reviewed.
- It is not a decision to use React, Vite or MapLibre in the final application. Choosing an art direction, user workflow, final UI stack and production serving/CSP model still requires owner review.
- Trusted geographic data, historical rights and parcel/building precision are entirely unresolved. Do not put source-backed investigations on an invented map.
