import { useEffect, useState } from 'react';
import { adaptInvestigation, adaptShortlist, type InvestigationView, type ShortlistView } from './evidenceBridge';
import './sourceReview.css';

type FixtureCase = { key: 'supported' | 'insufficient'; label: string; investigation_id: string };
type FixtureIndex = { source_kind: 'synthetic_fixture'; cases: FixtureCase[]; shortlist_id: string };
type Tab = 'investigation' | 'shortlist';
type Loading = 'loading' | 'ready' | 'failed';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

async function readJson(path: string, signal: AbortSignal): Promise<unknown> {
  if (!path.startsWith('/') || path.startsWith('//')) throw Error('invalid_local_path');
  const response = await fetch(path, { method: 'GET', cache: 'no-store', credentials: 'same-origin', signal });
  if (!response.ok) throw Error('Local fixture service returned HTTP ' + response.status);
  return await response.json() as unknown;
}

function parseIndex(data: unknown): FixtureIndex {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw Error('invalid_fixture_index');
  const raw = data as Record<string, unknown>;
  if (raw.source_kind !== 'synthetic_fixture' || !UUID.test(String(raw.shortlist_id)) ||
      !Array.isArray(raw.cases) || raw.cases.length !== 2) {
    throw Error('invalid_fixture_index');
  }
  const options: FixtureCase[] = [];
  for (const value of raw.cases) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error('invalid_fixture_option');
    const item = value as Record<string, unknown>;
    if ((item.key !== 'supported' && item.key !== 'insufficient') ||
        typeof item.label !== 'string' || item.label.length > 120 ||
        !UUID.test(String(item.investigation_id))) throw Error('invalid_fixture_option');
    options.push({key: item.key, label: item.label, investigation_id: item.investigation_id as string});
  }
  if (new Set(options.map(item => item.key)).size !== 2 ||
      new Set(options.map(item => item.investigation_id)).size !== 2) throw Error('duplicate_fixture_option');
  return { source_kind: 'synthetic_fixture', cases: options, shortlist_id: raw.shortlist_id as string };
}

function readableStatus(value: InvestigationView['status']): string {
  return ({
    supported_neighbourhood: 'Supported neighbourhood evidence',
    exploratory_spatial: 'Exploratory sales only',
    insufficient_data: 'Insufficient data',
    out_of_coverage: 'Outside supported scope',
  })[value];
}

function Money({value, context}: {value:string; context:string}) {
  return <div className="source-money"><strong>{value}</strong><span>{context}</span></div>;
}

export default function SourceReview() {
  const [index, setIndex] = useState<FixtureIndex | null>(null);
  const [indexError, setIndexError] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [investigation, setInvestigation] = useState<InvestigationView | null>(null);
  const [investigationState, setInvestigationState] = useState<Loading>('loading');
  const [investigationError, setInvestigationError] = useState('');
  const [selectedSale, setSelectedSale] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('investigation');
  const [shortlist, setShortlist] = useState<ShortlistView | null>(null);
  const [shortlistState, setShortlistState] = useState<Loading>('loading');
  const [shortlistError, setShortlistError] = useState('');
  const [shortlistRevision, setShortlistRevision] = useState(0);
  const [investigationRevision, setInvestigationRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    readJson('/_study/cases', controller.signal).then(value => {
      if (controller.signal.aborted) return;
      const parsed = parseIndex(value);
      setIndex(parsed);
      setSelectedId(parsed.cases[0]!.investigation_id);
    }).catch(error => {
      if (!controller.signal.aborted) setIndexError(error instanceof Error ? error.message : 'Fixture index unavailable');
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    const controller = new AbortController();
    setInvestigation(null);
    setSelectedSale(null);
    setInvestigationState('loading');
    setInvestigationError('');
    readJson('/v1/investigations/' + selectedId, controller.signal).then(raw => {
      if (controller.signal.aborted) return;
      const view = adaptInvestigation(raw);
      if (view.investigationId !== selectedId) throw Error('investigation_identity_conflict');
      setInvestigation(view);
      setInvestigationState('ready');
    }).catch(error => {
      if (!controller.signal.aborted) {
        setInvestigation(null);
        setInvestigationState('failed');
        setInvestigationError(error instanceof Error ? error.message : 'Evidence unavailable');
      }
    });
    return () => controller.abort();
  }, [selectedId, investigationRevision]);

  useEffect(() => {
    if (!index || tab !== 'shortlist') return;
    const controller = new AbortController();
    setShortlist(null);
    setShortlistState('loading');
    setShortlistError('');
    readJson('/v1/shortlists/' + index.shortlist_id, controller.signal).then(raw => {
      if (controller.signal.aborted) return;
      const parsed = adaptShortlist(raw);
      if (parsed.shortlistId !== index.shortlist_id) throw Error('shortlist_identity_conflict');
      setShortlist(parsed);
      setShortlistState('ready');
    }).catch(error => {
      if (!controller.signal.aborted) {
        setShortlist(null);
        setShortlistState('failed');
        setShortlistError(error instanceof Error ? error.message : 'Shortlist unavailable');
      }
    });
    return () => controller.abort();
  }, [index, tab, shortlistRevision]);

  const selected = investigation?.comparables.find(sale => sale.uiKey === selectedSale);
  return <div className="source-shell" data-testid="source-review">
    <header className="source-topbar"><div className="source-brand"><span className="source-mark">▥</span><span>houseprice <b>INTELLIGENCE</b></span></div><div className="source-server-badge">LOCAL PYTHON API · FIXTURES ONLY</div></header>
    <div className="source-container">
      <nav className="source-breadcrumb" aria-label="Location in concept"><a href="/">Spatial lab</a><span>/</span><b>Source-connected review</b><span className="source-separator">·</span><span>Read-only experiment</span></nav>
      <section className="source-intro"><div><div className="source-eyebrow">Evidence integration / 01</div><h1>Trust the records.<br/><em>Not the decoration.</em></h1><p>This screen reads frozen fictional investigations from the actual local Python API. It displays recorded sale evidence, not property predictions.</p></div><div className="source-meta"><span>API: p3-draft-v0.3</span><span>Mode: read-only</span></div></section>
      <div className="source-warning" role="note">This is an isolated fictional-data review. No real properties, verified map locations, accounts or current valuations are available. The main HPI application has not been replaced.</div>
      {indexError && <div className="source-error" role="alert" data-testid="source-index-error">Cannot load this fictional demo: {indexError}</div>}
      {!index && !indexError && <p role="status" data-testid="source-index-loading">Loading fixture investigation identifiers…</p>}
      {index && <>
        <div className="source-toolbar"><div className="source-tabbar" role="group" aria-label="Connected research views">
          <button type="button" aria-pressed={tab === 'investigation'} onClick={() => setTab('investigation')}>Investigation</button>
          <button type="button" aria-pressed={tab === 'shortlist'} onClick={() => setTab('shortlist')}>Saved comparison</button>
        </div><div className="source-toolbar-caption">Source: synthetic fixture SQLite · All prices USD</div></div>
        {tab === 'investigation' && <>
          <div className="source-casebar" role="group" aria-label="Saved fictional investigations">
            {index.cases.map(item => <button key={item.key} type="button" data-testid={'source-case-' + item.key} aria-pressed={selectedId === item.investigation_id}
              onClick={() => setSelectedId(item.investigation_id)}><span className="source-case-icon">{item.key === 'supported' ? '01' : '02'}</span><span><strong>{item.label}</strong><small>{item.key === 'supported' ? 'Earlier sales available' : 'No eligible earlier sales'}</small></span></button>)}
          </div>
          {investigationState === 'loading' && <div role="status" data-testid="source-investigation-loading" className="source-info-state">Loading source-verified fictional evidence…</div>}
          {investigationState === 'failed' && <div role="alert" data-testid="source-investigation-error" className="source-error">The frozen investigation could not be verified: {investigationError}<button type="button" onClick={() => setInvestigationRevision(x => x+1)}>Retry</button></div>}
          {investigation && investigationState === 'ready' && <>
            <section className="source-summary"><div><div className="source-eyebrow">Saved investigation / server verified</div><h2 data-testid="source-subject">{investigation.subjectLabel}</h2><p>Fictional parcel {investigation.subjectPin ?? 'unresolved'} · Building identity not verified</p></div><div className="source-summary-numbers">
              <Money value={investigation.askingPriceText} context="User-reported asking price"/>
              <div className="source-stat"><strong data-testid="source-count">{investigation.selectedCount}</strong><span>Eligible prior sales</span></div>
              <div className="source-stat status-stat"><strong data-testid="source-status">{readableStatus(investigation.status)}</strong><span>Evidence classification</span></div>
            </div></section>
            <div className="source-workbench">
              <section className="source-geo-panel" aria-label="Unavailable verified geographic map"><div className="source-panel-head"><strong>Location intelligence</strong><small>VERIFIED GEOMETRY NOT PROVIDED</small></div>
                <div className="source-map-off" data-testid="source-map-unavailable"><div className="source-map-symbol" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="20" cy="20" r="9"/><path d="M20 2v8M20 30v8M2 20h8M30 20h8"/><circle cx="20" cy="20" r="2" fill="currentColor" stroke="none"/></svg></div><p className="source-map-kicker">MAP WITHHELD</p><h3>Location unavailable.</h3><p>No approved geographic features are attached to this saved investigation. Displaying arbitrary property pins here would be misleading.</p><span>NO COORDINATES · NO DISTANCE CLAIMS</span></div>
                <div className="source-geo-footer"><span>Parcel identity ≠ verified building</span><span>Map renderer disabled</span></div>
              </section>
              <section className="source-evidence" aria-label="Saved comparable sale evidence"><div className="source-panel-head"><strong>Recorded sale evidence</strong><small>{investigation.selectedCount} SOURCE-LINKED SALES</small></div>
                {investigation.comparables.length > 0 ?
                <div className="source-sale-list" data-testid="source-sale-list">{investigation.comparables.map(sale => <button key={sale.uiKey} data-testid="source-sale" aria-pressed={selectedSale === sale.uiKey} type="button" onClick={() => setSelectedSale(sale.uiKey)}>
                  <span className="source-sale-rank">{String(sale.rank).padStart(2,'0')}</span><span className="source-sale-main"><strong>{sale.document}</strong><small>Recorded {sale.saleDate} · Parcel {sale.pin}</small></span><span className="source-sale-price">{sale.priceText}<small>Completed sale</small></span>
                </button>)}</div> :
                <div className="source-empty" data-testid="source-insufficient"><span>∅</span><h3>No qualifying earlier sales.</h3><p>The saved investigation cannot support a comparison price. This is not a zero-dollar valuation.</p><small>Backend reason: {investigation.reason ?? 'No qualifying data'}</small></div>}
                <div className="source-sale-detail" role="status" aria-live="polite"><small>EXPLANATION</small><p data-testid="source-sale-reason">{selected ? selected.explanation : investigation.comparables.length > 0 ? 'Select a recorded sale to read its original matching explanation. No map location is available.' : 'Insufficient evidence is a valid result. No valuation has been produced.'}</p></div>
              </section>
            </div>
            <div className="source-bottom-grid"><section className="source-bottom-card"><div className="source-eyebrow">Evidence provenance</div><h3>A frozen view, not a fresh calculation.</h3><dl><div><dt>Curated fixture build</dt><dd data-testid="source-build">{investigation.sourceBuildId}</dd></div><div><dt>Source snapshots</dt><dd data-testid="source-snapshots">{investigation.sourceSnapshotIds.join(', ')}</dd></div><div><dt>Analysis date</dt><dd>{investigation.analysisDate}</dd></div><div><dt>Rule selection tier</dt><dd>{investigation.tier}</dd></div></dl></section>
              <section className="source-bottom-card"><div className="source-eyebrow">Limitations and warnings</div><h3>What the evidence cannot tell you.</h3><p data-testid="source-warning">The server returned no current valuation. Source updates and historical publication timing require separate verification.</p>{investigation.warnings.map((w,i) => <p className="source-api-warning" key={i}>{w}</p>)}</section></div>
          </>}
        </>}
        {tab === 'shortlist' && <section className="source-shortlist" data-testid="source-shortlist"><div className="source-shortlist-heading"><div><div className="source-eyebrow">Frozen source evidence / mutable notes</div><h2>Saved comparison</h2><p>These are genuine saved fictional shortlist entries from the local API. Notes are displayed but cannot be edited in this review.</p></div><button type="button" className="source-refresh" onClick={() => setShortlistRevision(v => v+1)}>Refresh saved data</button></div>
          {shortlistState === 'loading' && <p role="status" data-testid="source-shortlist-loading">Rechecking saved evidence and notes…</p>}
          {shortlistState === 'failed' && <div role="alert" data-testid="source-shortlist-error" className="source-error">Cannot verify shortlist: {shortlistError}</div>}
          {shortlist && shortlistState === 'ready' && <div className="source-shortlist-grid">{shortlist.entries.map(entry => <article className="source-shortlist-card" key={entry.investigationId} data-testid="source-shortlist-entry"><span className="source-eyebrow">Source-backed fictional parcel</span><h3>{entry.investigation.subjectLabel}</h3><p className="source-shortlist-status">{readableStatus(entry.investigation.status)}</p><Money value={entry.investigation.askingPriceText} context="User-reported asking price"/><div className="source-shortlist-count">{entry.investigation.selectedCount} source-linked earlier sales</div><div className="source-note"><small>SAVED NOTE · READ-ONLY</small><p>{entry.noteText || 'No note recorded.'}</p></div><button type="button" onClick={() => {setSelectedId(entry.investigationId);setTab('investigation')}}>Inspect frozen evidence</button></article>)}</div>}
        </section>}
      </>}
      <footer className="source-footer"><b>HOUSE PRICE INTELLIGENCE / SOURCE LAB</b><span>Local-only, read-only · No trustworthy map coordinates · No price model</span></footer>
    </div>
  </div>;
}
