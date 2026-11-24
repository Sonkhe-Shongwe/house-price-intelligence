import { Component, lazy, Suspense, useEffect, useState, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import SchematicMap from './SchematicMap';
import { subjects, type SaleId, type SubjectId, type ExampleSale } from './data';
import './style.css';

const VectorMap = lazy(() => import('./VectorMap'));
const SourceReview = lazy(() => import('./SourceReview'));
type View = 'investigate' | 'compare' | 'methodology';
type Theme = 'editorial' | 'intelligence';
type Renderer = 'schematic' | 'vector';

class MapImportBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError(): { failed: boolean } {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return <div className="map-stage"><div className="renderer-fallback" role="status" data-testid="webgl-fallback">
        <strong>Optional map unavailable</strong>
        <p>The WebGL module could not load. The same evidence remains accessible in the comparable list, or switch back to the SVG diagram.</p>
      </div></div>;
    }
    return this.props.children;
  }
}

function IconHouse() {
  return <svg viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M4 17L18 5l14 12v14H4V17z"/><path d="M13 31V20h10v11"/><path d="M7 10V5h6"/></svg>;
}

function App() {
  const [view, setView] = useState<View>('investigate');
  const [theme, setTheme] = useState<Theme>('editorial');
  const [renderer, setRenderer] = useState<Renderer>('schematic');
  const [subjectId, setSubjectId] = useState<SubjectId>('a');
  const [selected, setSelected] = useState<SaleId | null>(null);
  const [mobilePanel, setMobilePanel] = useState<'map' | 'evidence'>('map');
  const [noteA, setNoteA] = useState('');
  const [noteB, setNoteB] = useState('');
  const subject = subjects[subjectId];
  const chosen: ExampleSale | undefined = subject.sales.find(s => s.id === selected);

  useEffect(() => { setSelected(null); }, [subjectId]);
  useEffect(() => { document.documentElement.dataset.hpiTheme = theme; }, [theme]);

  function chooseSale(id: SaleId) {
    // This is only a UI selection. Eligibility and price are never recalculated.
    if (!subject.sales.some(s => s.id === id)) return;
    setSelected(id);
  }

  return <div className="shell">
    <header className="app-topbar">
      <button type="button" className="logo-button" onClick={() => setView('investigate')} aria-label="House Price Intelligence, go to investigation">
        <span className="logo-mark" aria-hidden="true"><i/><i/><i/></span>
        <span className="logo-words"><strong>houseprice</strong><small>INTELLIGENCE</small></span>
      </button>
      <nav className="primary-nav" aria-label="Prototype views">
        <button type="button" aria-current={view === 'investigate' ? 'page' : undefined} onClick={() => setView('investigate')}>Investigation</button>
        <button type="button" aria-current={view === 'compare' ? 'page' : undefined} onClick={() => setView('compare')}>Shortlist</button>
        <button type="button" aria-current={view === 'methodology' ? 'page' : undefined} onClick={() => setView('methodology')}>Methodology</button>
      </nav>
      <span className="global-demo-tag">FICTIONAL TECHNOLOGY STUDY</span>
    </header>

    <div className="app-main">
      <div className="project-trail"><span>PRODUCT LAB / SPATIAL EVIDENCE</span><span className="trail-divider">·</span><strong>TECHNOLOGY SPIKE 01</strong><div className="theme-controls" role="group" aria-label="Visual style"><button type="button" onClick={() => setTheme('editorial')} aria-pressed={theme === 'editorial'}>Editorial</button><button type="button" onClick={() => setTheme('intelligence')} aria-pressed={theme === 'intelligence'}>Intelligence</button></div></div>
      <div className="context-note" role="note"><span aria-hidden="true">✧</span><div><strong>Design laboratory, not a live property product.</strong> All streets, marker positions and prices are invented. Virtual map coordinates are <strong>not geographic property locations</strong>. Nothing here comes from the real data pipeline.</div></div>

      {view === 'investigate' && <>
        <div className="page-intro"><div><p className="eyebrow">BETTER QUESTIONS. STRONGER DECISIONS.</p><h1>A place for <em>evidence.</em></h1><p className="page-description">Understand each earlier-sale example in context. A sophisticated map should clarify the decision, never manufacture certainty.</p></div><button type="button" className="button-outline" onClick={() => setView('compare')}>Open shortlist <span aria-hidden="true">↗</span></button></div>
        <div className="subject-bar">
          <div className="subject-persona"><div className="house-icon"><IconHouse /></div><div><small>SUBJECT PROPERTY · FICTIONAL PARCEL</small><h2 data-testid="subject-name">{subject.label}</h2><p>Demonstration District · Building identity not verified</p></div></div>
          <div className="subject-stats"><div><small>USER-REPORTED ASK</small><strong>{subject.askingText}</strong></div><div><small>ELIGIBLE EARLIER SALES</small><strong data-testid="eligible-count">{subject.sales.length} records</strong></div><div><small>EVIDENCE STATUS</small><strong className={subject.status === 'insufficient_data' ? 'warning' : 'success'}>{subject.status === 'insufficient_data' ? '● Insufficient' : '● Supported (demo)'}</strong></div></div>
        </div>
        <div className="lab-toolbar"><div className="lab-heading"><p className="section-eyebrow">SPATIAL EVIDENCE EXPLORER</p><h3>Every pin needs a reason.</h3><span>Choose a numbered example to inspect its context.</span></div><div className="toolbar-right"><div className="segmented" role="group" aria-label="Map renderer"><button type="button" data-testid="choose-svg" aria-pressed={renderer === 'schematic'} onClick={() => setRenderer('schematic')}>Schematic SVG</button><button type="button" data-testid="choose-vector" aria-pressed={renderer === 'vector'} onClick={() => setRenderer('vector')}>MapLibre WebGL</button></div><button type="button" className="button-outline small" data-testid="switch-subject" onClick={() => setSubjectId(s => s === 'a' ? 'b' : 'a')}>{subjectId === 'a' ? 'Show no-evidence case' : 'Show supported case'}</button></div></div>
        <div className="mobile-switch" role="group" aria-label="Mobile content"><button type="button" onClick={() => setMobilePanel('map')} aria-pressed={mobilePanel === 'map'}>Map</button><button type="button" onClick={() => setMobilePanel('evidence')} aria-pressed={mobilePanel === 'evidence'}>Evidence</button></div>
        <div className={`workbench workbench-${mobilePanel}`}>
          <section className="map-panel" aria-label="Map renderer proof"><div className="panel-topline"><strong>{renderer === 'schematic' ? 'Illustrative district' : 'Local vector rendering laboratory'}</strong><span>DISPLAY ONLY · NOT TO SCALE</span></div>
            {renderer === 'schematic' ? <SchematicMap subject={subject} selectedSale={selected} onSelect={chooseSale} /> : <MapImportBoundary key={`vector-${subjectId}`}><Suspense fallback={<div className="map-stage loader" role="status">Loading the optional WebGL renderer…</div>}><VectorMap subject={subject} selectedSale={selected} onSelect={chooseSale}/></Suspense></MapImportBoundary>}
            <div className="map-bottom"><span><i className="key-subject"/> Subject parcel</span><span><i className="key-sale"/> Earlier sale</span><span className="map-bottom-detail">Visual only. No distance, journey time or valuation.</span></div>
          </section>
          <aside className="evidence-panel"><div className="panel-topline"><strong>Selected comparable evidence</strong><span>{subject.sales.length} OF 3 AVAILABLE</span></div>
            <div className="panel-explainer">{subject.sales.length ? 'The fictional sales below form a fixed example evidence set. Clicking the map does not recompute eligibility.' : 'No completed-sale evidence qualifies for this fictional subject. Its map position cannot supply missing sales.'}</div>
            {subject.sales.length ? <div className="evidence-list" data-testid="evidence-list">{subject.sales.map(sale => <button key={sale.id} type="button" className={`evidence-option ${selected === sale.id ? 'chosen' : ''}`} onClick={() => chooseSale(sale.id)} aria-pressed={selected === sale.id} data-testid={`evidence-${sale.id}`}><span className="evidence-number">{sale.rank.toString().padStart(2, '0')}</span><span className="evidence-title"><strong>{sale.label}</strong><small>{sale.date} · {sale.buildingAreaText}</small></span><span className="evidence-price">{sale.priceText}<small>completed sale · invented</small></span></button>)}</div> : <div className="evidence-unavailable" data-testid="insufficient-evidence"><span className="empty-glyph" aria-hidden="true">∅</span><h3>Not enough evidence.</h3><p>We cannot infer a current value from missing comparable records. This outcome should be as clear as a supported result.</p></div>}
            <div className="selection-insight" role="status" aria-live="polite"><span>DETAIL / EVIDENCE EXPLANATION</span><p data-testid="selected-reason">{chosen ? chosen.reason : subject.sales.length ? 'Choose a sale marker or list item to inspect the illustration.' : 'No qualified sales exist in this demonstration. No zero-valued property is implied.'}</p></div>
          </aside>
        </div>
        <div className="below-grid"><article className="info-module"><span className="module-label">01 / EVIDENCE INTEGRITY</span><h3>Price is a fact. Confidence is earned.</h3><p>Each fictional sale amount is displayed as supplied text. The original app's matcher, source snapshots and eligibility rules belong on the Python side, not inside the map renderer.</p><div className="info-stats"><div><b>{subject.sales.length}</b><small>illustrative sales</small></div><div><b>None</b><small>predicted values</small></div><div><b>Parcel</b><small>identity scope</small></div></div></article><article className="info-module"><span className="module-label">02 / MAPPING TECHNOLOGY</span><h3>Visual polish without hidden data claims.</h3><p>The SVG diagram is the reliable accessible baseline. The alternative MapLibre view runs entirely from inline fictional geometry and tests WebGL2, the bundled worker and component cleanup.</p><button type="button" className="inline-action" onClick={() => setView('methodology')}>Explore technical limitations <span aria-hidden="true">↗</span></button></article></div>
      </>}

      {view === 'compare' && <><div className="page-intro"><div><p className="eyebrow">YOUR RESEARCH, IN ONE PLACE</p><h1>Compare without <em>guessing.</em></h1><p className="page-description">Two invented homes. One has comparable evidence and the other does not. The comparison preserves that difference rather than hiding it.</p></div><button className="button-outline" type="button" onClick={() => setView('investigate')}>Return to investigation ↗</button></div>
        <div className="shortlist-grid">
          {(['a', 'b'] as const).map((id, i) => { const item = subjects[id]; const val = id === 'a' ? noteA : noteB; const setter = id === 'a' ? setNoteA : setNoteB; return <article className="shortlist-entry" key={id}><span className="module-label">PROPERTY {i + 1} / FICTIONAL</span><h2>{item.label}</h2><p className={`evidence-signal ${item.sales.length ? '' : 'warning'}`}>{item.sales.length ? '● Earlier-sale examples available' : '● Insufficient earlier-sale evidence'}</p><div className="shortlist-price">{item.askingText}<small>Buyer-entered asking price</small></div><label htmlFor={`note-${id}`}>Your notes for this design study</label><textarea id={`note-${id}`} value={val} onChange={event => setter(event.target.value)} maxLength={800} placeholder="Write a thought about this imaginary property" /><p className="note-disclosure">This draft exists in memory only and is not saved or account-private.</p><button type="button" className="inline-action" onClick={() => { setSubjectId(id); setView('investigate'); }}>Inspect evidence ↗</button></article>; })}
        </div>
        <div className="compare-table-wrap"><table className="compare-table"><caption>Illustrative side-by-side comparison. Every value is invented.</caption><thead><tr><th scope="col">Research dimension</th><th scope="col">101 Fictional Way</th><th scope="col">105 Fictional Court</th></tr></thead><tbody><tr><th scope="row">Buyer asking price</th><td>$500,000</td><td>$610,000</td></tr><tr><th scope="row">Eligible earlier sales</th><td>3 invented sales</td><td>0</td></tr><tr><th scope="row">Evidence category</th><td>Supported (illustrative)</td><td>Insufficient data</td></tr><tr><th scope="row">Verified building location</th><td>Not available</td><td>Not available</td></tr><tr><th scope="row">Current valuation</th><td>Not produced</td><td>Not produced</td></tr></tbody></table></div>
      </>}

      {view === 'methodology' && <><div className="page-intro"><div><p className="eyebrow">WHEN NOT TO TRUST A PRETTY MAP</p><h1>Show the limits. <em>Earn trust.</em></h1><p className="page-description">This detached technology experiment answers a narrow question: can an expressive, typed frontend integrate a performant map without corrupting sale evidence?</p></div></div><div className="methods"><article><span className="module-label">GEOGRAPHY</span><h2>Coordinates are fictional test vectors</h2><p>The original repository fixture uses identical coordinates for six fictional parcels. This spike instead maps independent percentages into virtual MapLibre coordinates solely to test a renderer. No surveyed property positions, distances, geocoding or external map tiles are supplied.</p></article><article><span className="module-label">SOFTWARE BOUNDARY</span><h2>No production frontend migration</h2><p>React, TypeScript, Vite and MapLibre live only in this isolated study. The production-like Python/SQLite fixture application and frozen evidence remain unchanged. Framework selection remains unapproved.</p></article><article><span className="module-label">PERFORMANCE / ACCESSIBILITY</span><h2>What a credible selection requires</h2><p>Keyboard-accessible comparable controls, reduced-motion handling, narrow-screen reflow, no-GPU fallback, worker/CSP compatibility, bundle measurement, dependency lock and real-browser tests. This spike is not a full accessibility audit or a live geographic map.</p></article><article><span className="module-label">BEFORE REAL DATA</span><h2>Map source, rights and precision come first</h2><p>A real geographic view will need a source-owned map API with stable IDs, history, verified geometry, parcel-versus-building identity, source-rights checks, attribution and licensed tiles. A map renderer cannot establish any of those facts.</p></article></div></>}
      <footer className="footer"><strong>HPI / SPATIAL LAB</strong><span>React + TypeScript + Vite · SVG versus local MapLibre · 100% invented examples</span><span>Not the released House Price Intelligence app</span></footer>
    </div>
  </div>;
}

createRoot(document.getElementById('root')!).render(
  window.location.pathname === '/source-review'
    ? <Suspense fallback={<main role="status" className="source-info-state">Loading local evidence interface…</main>}><SourceReview /></Suspense>
    : <App />
);
