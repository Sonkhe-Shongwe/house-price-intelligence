# HPI acquisition and intelligence engine | Side directive (AE0)
 
26 November 2026. Owner requested recording the proposed direction separately and testing it. This is a bounded P0.4/P0.7 feasibility experiment, not adoption of a new architecture, product scope, market, live acquisition permission or replacement roadmap. Existing P0-G blocker and all P0-P8 gates remain. Strict R0. See [checkpoint](../CHECKPOINT.md), [Data Manager](DATA_MANAGER_V1.md), [lean directive](LEAN_ENGINEERING_DIRECTIVE.md) and [acquisition register](../research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md).
 
## Purpose and architectural position
 
Move beyond searching for convenient downloads: discover legitimate structured APIs, public catalogues, permitted HTML tables, GIS services, documents and archives; acquire only under exact source policies; normalise and validate; construct independently reproducible intelligence. The product remains Investigate / Compare / Decide, two-to-three-property shortlist, not an infrastructure platform for its own sake. Completed transactions and authoritative property identity remain indispensable to comparable sales; context cannot substitute. Keep asking, completed sale, valuation and model estimate distinct. No assumption that a public API, robots permission or academic access grants retention, joins or publication.
 
Retain the current Python Data Manager (2,667 lines at reviewed 9147fc4), its six registrations, manifests, CLI, private sibling workspace, hashes, offline audit, source-specific PDF/geospatial parsing and exact Treasury approval/attempt history. Treasury 007 is parked, consumed attempts cannot replay. Prefer modular Python with isolated parsing workers as justified, not a rewrite. Source-specific semantics are necessary; only share mechanics after two genuine uses.
 
Logical pipeline: discovery metadata -> source policy and explicit acquisition scope -> bounded job/attempt/request ledger -> source adapter -> private staging (Bronze) -> strict validation and normalisation (Silver) -> independently approved entity relationships and derived intelligence (Gold) -> publication eligibility -> existing buyer application. Bronze/Silver/Gold are logical boundaries, not new cloud databases. Preserve previous accepted versions; no raw/derived private data in Git/CI, no automatic deletion or renewal, no cloud write or scheduling by implication.
 
## Technology choices for evaluation, not approved dependencies
 
| Concern | Initial direction | Alternatives and stop condition |
| --- | --- | --- |
| HTTP/API | Existing standard library bounded HTTPS; consider HTTPX streaming | Scrapy only for multiple permitted crawls; no generic arbitrary URLs |
| HTML/browser | BeautifulSoup or lxml when justified; existing Playwright for exceptional authorised dynamic pages | No Selenium duplication, access evasion or automated terms assent |
| Documents | Existing pypdf; evaluate pdfplumber | PyMuPDF licensing review; OCR only if needed |
| GIS | Existing Shapely/PyProj; conditional GeoPandas, GDAL, GeoParquet | Verify CRS, history, positional accuracy and licence; no blind spatial joins |
| Storage | Existing files/manifests; SQLite for durable job state if needed; Parquet/DuckDB for larger analytical workloads | Retain PostgreSQL serving; no national raw warehouse in Neon |
| Orchestration | Small deterministic coordinator | Compare dlt incremental/schema controls and Scrapy; Prefect/Dagster only on demonstrated need; no Airflow, Spark, Kafka, Kubernetes or Redis initially |
| AI | Research and mapping suggestions only | No arbitrary execution, permission minting or invented data |
 
Reference documentation: [HTTPX](https://www.python-httpx.org/), [Scrapy](https://docs.scrapy.org/en/latest/), [Playwright](https://playwright.dev/python/), [dlt](https://dlthub.com/docs/), [DuckDB](https://duckdb.org/docs/stable/), [DCAT](https://www.w3.org/TR/vocab-dcat-3/), [ArcGIS query](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/), [OWASP SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html), [Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309), [POPIA](https://www.gov.za/documents/protection-personal-information-act). These are engineering reference leads, not new source licences or runtime evidence.
 
## Contracts and risks
 
Source policy must bind publisher/version, exact interfaces/fields/geography, purpose, collection/retention/transform/join/display rights separately, expiry, request/byte/row/time limits and exact one-time authority. Default deny. Production transport must additionally verify TLS, allowlisted destination and resolved IPs, redirects, proxy and DNS rebinding controls, bounded streamed/decompressed bytes and total deadlines; parser sandbox/resource controls, no external entities, archive traversal, formula injection or untrusted execution. Reject unexpected sensitive fields; do not assume redaction anonymises property records. Minimise logs and data; no automatic retries on access denial, schema drift or consumed scope. Durable state and crash-safe commit/reconciliation must be demonstrated before live use. Keep raw bytes only when permitted. Treat source date, observation, publication, acquisition and validity intervals separately; hashes attest integrity, not accuracy or rights.
 
Canonical entities: source/version/policy/approval/job/attempt/request/snapshot/dataset/version/quality/transformation/lineage/publication eligibility. Property, address, parcel, building, transaction, valuation, listing and area context are separate grains. Exact authoritative shared keys and verified mappings outrank spatial/text candidates; ambiguous match abstains. Footprint is not floor area; parcel is not dwelling; area statistics are not household reliability. Preserve exact money, earlier-only sales, unique comparable PIN, price-free ranking and supported-class abstention.
 
Candidate sequence: D01 sales and D02 cadastre remain critical independent unresolved work; D04 address linkage essential. D11 schools (DataFirst 985, 2023 master list) and GCRO aggregate chart exports are candidate contextual routes; exact licence, data projection, definitions, vintage, size and uncertainty must be qualified. Cape Town GIS metadata, OSM extracts, environment, municipal services and development follow only demonstrated buyer value. No respondent microdata, restricted portal scraping, proxy rotation, CAPTCHA bypass, demographic desirability scoring, nationwide collection, unapproved join or paid fallback. Existing 006/008 source-specific proof remains valid at its scope.
 
## AE0-AE8 proposed subordinate sequence
 
| Step | Exit evidence |
| --- | --- |
| AE0 architecture and feasibility | Bounded proof and explicit retain/refactor/replace review |
| AE1 foundations | Existing CLI/manifest/registration parity, shared controls proven useful |
| AE2 safe transport | Real transport negative controls, policy enforcement, resource and recovery proof |
| AE3 adapters | Two relevant qualified interfaces, independently verified acquisition |
| AE4 validation | Exact canonical semantics, version and provenance, schema-drift refusal |
| AE5 incremental | Durable budget/checkpoint/restart and duplicate prevention |
| AE6 identity | Approved sources, time-aware relationships, ambiguity/abstention |
| AE7 intelligence | Independently checked calculations, limitations and value |
| AE8 application | Approved data projection and integrated buyer journey |
 
No step implies authority for subsequent work. AE0 experiment is a named P0 feasibility dependency; later steps parked pending owner architectural review and applicable phase/rights gates. No automatic phase credit. Measure row counts, request counts, bytes, runtime, peak memory and disk only when actually tested; no national-scale inference. R0 local workspace and standard public synthetic CI; no self-hosted public runner or private records in artifacts. Free infrastructure limits and Windows storage must be measured before scale.
 
## AE0 first proof contract
 
The isolated [proof](../../tools/acquisition_feasibility.py) is intentionally not a production scraper. It has no real transport, URLs, filesystem writes, source registration, network client or dependencies. Two invented response formats (two JSON pages and one CSV page) share a bounded reader, exact source/format policy, strict row contract and in-memory single-use attempt. Exact row IDs stay strings; validate counts and duplicate identifiers within a source, generate deterministic source-specific aggregates and per-response SHA-256; never join or infer property values. Fixed approved fixture page IDs, response and cumulative byte cap, request and row cap. Stop on wrong page/format, malformed/duplicate JSON keys, wrong columns, extra fields, invalid count, duplicate ID, missing page, byte/request/row limit or reused attempt. Do not return partial output. No production authorisation semantics inferred from this in-memory proof. Test suite runs under existing backend fixture CI, not a new workflow. Local Windows data untouched.
 
Acceptance: both formats yield hand-checked independent totals and exact hashes; failures refuse with no partial published output and no subsequent request after rejection; consumed attempt cannot replay. Scope deliberately excludes HTML/GIS/browser transport, durable approvals/storage, actual source access, benchmarks, schema discovery and application integration. Next only after proof: qualify one exact legitimate structured source (prefer nonpersonal aggregate or institutional amenities) and propose a separate capped real-source experiment; if rights/size unavailable, stop or choose another qualified route. No P1 or scope/score change.
