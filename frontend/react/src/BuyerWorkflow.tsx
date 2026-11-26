import {ActionButton,Field,StatusMessage} from './UI';
import Icon from './Icon';
/** Source-owned fictional buyer journey. Deliberately no map geometry or price prediction. */
import {useEffect, useRef, useState} from 'react';
import {adaptInvestigation, type InvestigationView} from './evidenceBridge';
import './sourceReview.css';
import './buyerWorkflow.css';
import SavedComparison from './SavedComparison';
import GeoMapPanel from './GeoMapPanel';
import HistoryPanel from './HistoryPanel';
import Methodology from './Methodology';
import BuyerEvidencePreview from './BuyerEvidencePreview';
import EvidenceProfile from './EvidenceProfile';
import WorkspaceNavigation,{type WorkspaceView as View} from './WorkspaceNavigation';
import './workspaceShell.css';
import {fixtureFetch} from './fixtureFetch';

type Candidate = {
  addressId: string; label: string; hint: string | null; ambiguous: boolean;
};
type Chosen = Candidate & { pin: string };
type Phase = 'idle' | 'searching' | 'resolving' | 'creating' | 'reopening';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const PIN = /^\d{14}$/;
const QUERY = /^[A-Za-z0-9][A-Za-z0-9 .,'-]{1,79}$/;
const PRICE = /^(?:0|[1-9]\d{0,8})(?:\.\d{1,2})?$/;

async function request(path: string, signal: AbortSignal, payload?:unknown): Promise<unknown> {
  if(!path.startsWith('/') || path.startsWith('//')) throw Error('Invalid local route');
  const response = await fixtureFetch(path,{
    method:payload === undefined ? 'GET' : 'POST',
    cache:'no-store',credentials:'same-origin',signal,
    ...(payload === undefined ? {} : {headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)}),
  });
  let data:unknown;
  try {data=await response.json() as unknown;} catch {throw Error('Invalid API JSON response');}
  if(!response.ok){
    const body=data && typeof data==='object' && !Array.isArray(data)
      ? data as Record<string,unknown>:null;
    const message=body && typeof body.code==='string'&&typeof body.field==='string'
      ? body.field+': '+body.code
      : body && typeof body.error==='string'?body.error:'HTTP '+response.status;
    throw Error(message);
  }
  return data;
}
function asRecord(v:unknown):Record<string,unknown>{
  if(!v || typeof v!=='object' || Array.isArray(v)) throw Error('Invalid source response');
  return v as Record<string,unknown>;
}
function candidatesFrom(raw:unknown):Candidate[]{
  const value=asRecord(raw);
  if(value.source_kind!=='synthetic_fixture' || !['matches','no_match'].includes(String(value.status))
    || !Array.isArray(value.candidates) || value.candidates.length>8)
    throw Error('Unexpected address search contract');
  const seen=new Set<string>();
  return value.candidates.map((item:unknown)=>{
    const row=asRecord(item);
    if(typeof row.address_id!=='string'|| !/^[a-z0-9-]{1,40}$/.test(row.address_id)
      || typeof row.display_address!=='string'||row.display_address.length>120
      || row.identity_scope!=='parcel_only'||typeof row.ambiguous_address!=='boolean'
      || (row.ambiguous_address &&
        (typeof row.parcel_hint!=='string'||!row.parcel_hint.trim())))
      throw Error('Invalid parcel candidate');
    if(seen.has(row.address_id))throw Error('Duplicate parcel candidate');
    seen.add(row.address_id);
    return {addressId:row.address_id,label:row.display_address,
      hint:typeof row.parcel_hint==='string'?row.parcel_hint:null,
      ambiguous:row.ambiguous_address};
  });
}
function resolvedFrom(raw:unknown,candidate:Candidate):Chosen{
  const v=asRecord(raw);
  if(v.source_kind!=='synthetic_fixture' ||v.identity_status!=='synthetic_mapping_only'
     ||v.identity_scope!=='parcel_only'||v.building_identity_verified!==false
     ||v.address_id!==candidate.addressId||v.display_address!==candidate.label
     ||typeof v.pin!=='string'||!PIN.test(v.pin))
     throw Error('Resolved parcel identity did not match selected candidate');
  return {...candidate,pin:v.pin};
}
function presentError(error:unknown):string{
  return error instanceof Error?error.message:'The local fixture service is unavailable';
}
function statusLabel(s:InvestigationView['status']):string{
  return ({supported_neighbourhood:'Earlier neighbourhood sales available',
    exploratory_spatial:'Exploratory evidence only',
    insufficient_data:'Insufficient eligible evidence',
    out_of_coverage:'Outside fixture coverage'})[s];
}

export default function BuyerWorkflow(){
  const [view,setView]=useState<View>(window.location.pathname==='/buyer-workflow'?'investigate':'home');
  const [historyRevision,setHistoryRevision]=useState(0);
  const contentFocus=useRef<HTMLElement|null>(null);
  const previousView=useRef(view);
  useEffect(()=>{
    if(previousView.current!==view){
      previousView.current=view;
      contentFocus.current?.focus({preventScroll:true});
    }
  },[view]);
  const [query,setQuery]=useState('');
  const [candidates,setCandidates]=useState<Candidate[]>([]);
  const [chosen,setChosen]=useState<Chosen|null>(null);
  const [manualPin,setManualPin]=useState('');
  const [area,setArea]=useState('1600');
  const [price,setPrice]=useState('500000.00');
  const [analysisDate,setAnalysisDate]=useState('2024-07-01');
  const [phase,setPhase]=useState<Phase>('idle');
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const [record,setRecord]=useState<InvestigationView|null>(null);
  const [savedId,setSavedId]=useState('');
  const [reopenInput,setReopenInput]=useState('');
  const [activeRank,setActiveRank]=useState<number|null>(null);
  const sequence=useRef(0);
  const activeController=useRef<AbortController|null>(null);
  const pendingWrite=useRef(false);
  const writing=phase==='creating';

  const cancel=()=>{
    sequence.current++;
    activeController.current?.abort();
    activeController.current=null;
  };
  useEffect(()=>()=>{sequence.current++;activeController.current?.abort();},[]);
  const newOperation=()=>{
    cancel();
    const controller=new AbortController();
    activeController.current=controller;
    return {controller,seq:sequence.current};
  };
  const active=(seq:number,ctrl:AbortController)=>
    seq===sequence.current&&!ctrl.signal.aborted;

  function changeQuery(value:string){
    if(pendingWrite.current)return;
    cancel();setQuery(value);setManualPin('');setChosen(null);setCandidates([]);
    setRecord(null);setActiveRank(null);setError('');setMessage('');
    setPhase('idle');
  }
  async function search(event:React.FormEvent<HTMLFormElement>){
    event.preventDefault();
    if(pendingWrite.current)return;
    if(!QUERY.test(query.trim())){setError('Enter a fictional address containing 2–80 supported characters.');return;}
    const {controller,seq}=newOperation();
    setChosen(null);setManualPin('');setCandidates([]);setRecord(null);setActiveRank(null);
    setError('');setMessage('');setPhase('searching');
    try {
      const raw=await request('/v1/addresses/search',controller.signal,{query:query.trim()});
      const options=candidatesFrom(raw);
      if(!active(seq,controller))return;
      setCandidates(options);setMessage(options.length
        ? 'Choose a specific fictional parcel. Addresses can refer to more than one parcel.'
        : 'No invented addresses matched. Try Fictional Way or 105 Fictional Court.');
    }catch(e){if(active(seq,controller))setError('Address search failed: '+presentError(e));}
    finally{if(active(seq,controller))setPhase('idle');}
  }
  async function select(candidate:Candidate){
    if(pendingWrite.current)return;
    const {controller,seq}=newOperation();
    setError('');setChosen(null);setRecord(null);setActiveRank(null);
    setPhase('resolving');
    try{
      const raw=await request('/v1/addresses/'+encodeURIComponent(candidate.addressId),controller.signal);
      const resolved=resolvedFrom(raw,candidate);
      if(!active(seq,controller))return;
      setChosen(resolved);setCandidates([]);
      setMessage('Parcel selected. Building identity is unverified. Review the reported inputs before saving.');
    }catch(e){if(active(seq,controller))setError('Could not verify selected parcel: '+presentError(e));}
    finally{if(active(seq,controller))setPhase('idle');}
  }
  async function create(event:React.FormEvent<HTMLFormElement>){
    event.preventDefault();
    if(pendingWrite.current||(!chosen&&!PIN.test(manualPin)))return;
    const number=Number(area);
    if(!Number.isFinite(number)||number<=0||number>100000){
      setError('Enter a positive building area up to 100,000 ft².');return;
    }
    if(price!==''&&(!PRICE.test(price)||Number(price)<=0||Number(price)>1_000_000_000)){
      setError('Enter a positive asking price with up to two decimal places.');return;
    }
    if(!/^\d{4}-\d{2}-\d{2}$/.test(analysisDate)){
      setError('Select a valid analysis date.');return;
    }
    pendingWrite.current=true;
    const {controller,seq}=newOperation();
    setRecord(null);setActiveRank(null);setError('');setPhase('creating');
    const target=chosen??{pin:manualPin,addressId:null,label:'Fictional parcel '+manualPin};
    try{
      const original=await request('/v1/investigations',controller.signal,{
        township_code:'17',class_code:'203',analysis_date:analysisDate,
        subject:{pin:target.pin,...(target.addressId?{address_id:target.addressId}:{}),
          label:target.label,building_area_sqft:number,asking_price_usd:price||null}
      });
      const view=adaptInvestigation(original);
      if(view.subjectPin!==target.pin)throw Error('Created investigation has a different parcel identity');
      if(!active(seq,controller))return;
      setSavedId(view.investigationId);setReopenInput(view.investigationId);
      // Confirm the saved frozen result using the documented GET, no new matching.
      const reopened=adaptInvestigation(await request('/v1/investigations/'+view.investigationId,controller.signal));
      if(reopened.investigationId!==view.investigationId||reopened.subjectPin!==target.pin
        ||JSON.stringify(reopened)!==JSON.stringify(view))
        throw Error('Saved investigation did not reopen with identical evidence');
      if(!active(seq,controller))return;
      setRecord(reopened);setHistoryRevision(n=>n+1);
      setMessage('Saved and reopened through the Python fixture service. No valuation produced.');
    }catch(e){if(active(seq,controller))setError('Investigation unavailable: '+presentError(e)
      +'. If the server saved before an interruption, check Saved properties before repeating the write.');}
    finally{
      pendingWrite.current=false;
      if(active(seq,controller))setPhase('idle');
    }
  }
  async function reopen(event?:React.FormEvent<HTMLFormElement>,id?:string){
    event?.preventDefault();
    if(pendingWrite.current)return;
    const target=(id??reopenInput).trim();
    if(!UUID.test(target)){setError('Enter a valid lowercase saved investigation UUID.');return;}
    const {controller,seq}=newOperation();
    setError('');setRecord(null);setActiveRank(null);setPhase('reopening');
    try{
      const view=adaptInvestigation(await request('/v1/investigations/'+target,controller.signal));
      if(view.investigationId!==target)throw Error('Reopened the wrong saved investigation');
      if(!active(seq,controller))return;
      setRecord(view);setSavedId(view.investigationId);setReopenInput(view.investigationId);
      setChosen(null);setManualPin('');setCandidates([]);
      setMessage('Frozen investigation reopened without re-running matching.');
    }catch(e){if(active(seq,controller))setError('Could not reopen saved evidence: '+presentError(e));}
    finally{if(active(seq,controller))setPhase('idle');}
  }
  function navigate(next:View){
    if(pendingWrite.current)return;
    setView(next);
    window.scrollTo({top:0,behavior:'instant'});
  }
  function newInvestigation(){
    if(pendingWrite.current)return;
    cancel();setQuery('');setManualPin('');setChosen(null);setCandidates([]);
    setRecord(null);setActiveRank(null);setMessage('');setError('');setPhase('idle');
    setArea('1600');setPrice('500000.00');setAnalysisDate('2024-07-01');
    navigate('investigate');
  }
  function openHistory(id:string){navigate('investigate');void reopen(undefined,id);}
  const selected=record?.comparables.find(x=>x.rank===activeRank);
  return <div className="source-shell buyer-shell" data-testid="buyer-workflow">
    <header className="source-topbar"><div className="source-brand"><span className="source-mark">▥</span>
      <span>houseprice <b>INTELLIGENCE</b></span></div>
      <div className="source-server-badge">LOCAL-ONLY · FICTIONAL WORKSPACE</div></header>
    <a className="hpi-skip" href="#hpi-content">Skip to content</a>
    <div className="hpi-app-layout">
      <aside className="hpi-sidebar"><div className="hpi-nav-title">RESEARCH WORKSPACE</div>
        <WorkspaceNavigation view={view} onNavigate={navigate} disabled={writing}/>
        <div className="hpi-sidebar-note"><b>Local fixture</b><p>Fictional data only. No valuation or real locations.</p></div></aside>
      <main id="hpi-content" className="source-container hpi-main" ref={contentFocus} tabIndex={-1}>
        <div className="hpi-top-warning" role="note">Fictional data · Local-only workspace · No real property records or valuations</div>
        {(view==='home'||view==='saved')&&<HistoryPanel mode={view} revision={historyRevision} disabled={writing}
          onOpen={openHistory} onNew={newInvestigation} onCompare={()=>navigate('compare')} onHistory={()=>navigate('saved')}/>}
        {view==='methodology'&&<Methodology/>}
        <section hidden={view!=='investigate'} className="hpi-view" aria-label="Investigate">
      <section className="source-intro"><div><div className="source-eyebrow">The buyer journey / 02</div>
        <h1>Investigate a property.<br/><em>Understand the evidence.</em></h1>
        <p>Identify a parcel, inspect earlier completed sales and save a traceable investigation. This workspace uses fictional records only.</p>
      </div><div className="source-meta"><span>API · p3-draft-v0.3</span><span>Storage · local fixture database</span></div></section>
      <div className="source-warning" role="note">This is a fictional-only local application. Saved investigations use the selected local fixture database; do not enter personal information. A shared street address may represent two different parcels. No production account service, real property records, real map positions or current value estimates.</div>
      <section className="buyer-columns">
        <div className="buyer-forms">
          <article className="buyer-pane"><div className="buyer-section-number">01 / SEARCH</div>
            <h2>Identify the fictional parcel</h2><p>Search, then select a specific candidate. No house or building identity is presumed.</p>
            <form onSubmit={search} className="buyer-search-form">
              <label htmlFor="buyer-query">Address or street</label>
              <div className="buyer-input-row"><input data-testid="buyer-query" id="buyer-query"
                value={query} onChange={e=>changeQuery(e.target.value)}
                placeholder="Try an address in the active fictional build" autoComplete="off" maxLength={80}
                disabled={writing} required/>
                <ActionButton type="submit" data-testid="buyer-search" disabled={phase!=='idle'} icon="search" variant="primary">Search addresses</ActionButton>
              </div>
            </form>
            {phase==='searching'&&<StatusMessage data-testid="buyer-search-loading">Searching invented addresses…</StatusMessage>}
            {candidates.length>0&&<div className="buyer-candidates" role="group" aria-label="Distinct fictional parcel candidates">
              {candidates.map(c=><button key={c.addressId} type="button" data-testid="buyer-candidate"
                disabled={phase!=='idle'} onClick={()=>void select(c)}>
                <span className="buyer-candidate-symbol"><Icon name="parcel" size={22}/></span>
                <span><strong>{c.label}</strong>
                  <small>{c.ambiguous?c.hint:'Unique synthetic parcel candidate'} · Parcel only</small></span>
                <span className="buyer-candidate-select">Select</span>
              </button>)}</div>}
            {chosen && <div className="buyer-chosen" data-testid="buyer-selected-parcel"><b>Selected fictional parcel</b>
              <strong>{chosen.label}</strong><p>{chosen.hint??'Synthetic parcel'} · PIN {chosen.pin}</p>
              <span>Building identity not verified · Server-bound selection</span></div>}
            {phase==='resolving'&&<p role="status">Verifying candidate with the local Python API…</p>}
            <Field label="Or enter a fictional 14-digit parcel PIN" hint="Technical fixture lookup only. An unknown PIN may return insufficient evidence." id="buyer-manual-pin" data-testid="buyer-manual-pin" value={manualPin}
              inputMode="numeric" maxLength={14} disabled={writing}
              onChange={e=>{if(pendingWrite.current)return;cancel();setManualPin(e.target.value);
                setQuery('');setChosen(null);setCandidates([]);setRecord(null);setActiveRank(null);
                setError('');setMessage('');setPhase('idle');}}/>

          </article>
          <article className="buyer-pane"><div className="buyer-section-number">02 / INVESTIGATE</div>
            <h2>Review buyer-reported inputs</h2><p>Only the Python service can choose the earlier sales. This form does not calculate a price.</p>
            <form onSubmit={create} className="buyer-data-form">
              <div className="buyer-two-fields"><div><Field label="Building area (ft²)" id="buyer-area" data-testid="buyer-area" type="number" min="1" max="100000" step="1"
                  required value={area} onChange={e=>setArea(e.target.value)} disabled={writing}/></div>
                <div><Field label="Asking price, USD (buyer-reported)" id="buyer-price" data-testid="buyer-price" type="text" inputMode="decimal"
                  value={price} onChange={e=>setPrice(e.target.value)} disabled={writing}
                  placeholder="500000.00" maxLength={15}/></div></div>
              <Field label="Historical analysis date" id="buyer-date" data-testid="buyer-date" type="date" required value={analysisDate}
                onChange={e=>setAnalysisDate(e.target.value)} disabled={writing}/>
              <ActionButton className="buyer-save" type="submit" data-testid="buyer-create"
                disabled={(!chosen&&!PIN.test(manualPin)) || phase!=='idle'} icon="save" variant="primary">{phase==='creating'?'Saving and verifying…':'Save fictional investigation'}</ActionButton>
            </form>
            <div className="buyer-constraint">An address must be explicitly selected; a manually entered PIN is a separate lookup. Real geography remains unverified; a separate fictional display layer is optional.</div>
          </article>
        </div>
        <aside className="buyer-progress">
          <div className="buyer-section-number">RESEARCH WORKSPACE</div>
          <h2>Trace every decision.</h2><p>Server-owned parcel identity, source-verified comparable sales and reproducible saved results.</p>
          <div className="buyer-progress-line"><span className={chosen?'buyer-done':''}>1</span><div><b>Identify parcel</b><small>{chosen?'Specific synthetic PIN resolved':'Select a candidate from the search results'}</small></div></div>
          <div className="buyer-progress-line"><span className={record?'buyer-done':''}>2</span><div><b>Save source evidence</b><small>{record?'Frozen investigation reopened':'Send buyer inputs to the Python matcher'}</small></div></div>
          <div className="buyer-progress-line"><span>3</span><div><b>Do not infer location</b><small>Only opt-in virtual positions; no real-world location claims</small></div></div>
          <div className="buyer-reopen-card"><label htmlFor="buyer-reopen-id">Reopen saved investigation ID</label>
            <form onSubmit={reopen}><input id="buyer-reopen-id" data-testid="buyer-reopen-id" type="text"
              value={reopenInput} onChange={e=>setReopenInput(e.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" maxLength={36}/>
              <ActionButton type="submit" data-testid="buyer-reopen" disabled={phase!=='idle'} icon="open" variant="secondary">Reopen</ActionButton></form>
            <small>Saved IDs remain usable only while this local fixture database exists.</small></div>
        </aside>
      </section>
      {error&&<StatusMessage tone="error" className="source-error" data-testid="buyer-error">{error}</StatusMessage>}
      {message&&<StatusMessage tone="success" className="buyer-feedback" data-testid="buyer-feedback">{message}</StatusMessage>}
      {(phase==='reopening'||phase==='creating')&&<div role="status" data-testid="buyer-pending" className="source-info-state">Verifying source-owned evidence…</div>}
      {record&& <section className="buyer-result" data-testid="buyer-result"><div className="buyer-result-title">
        <div><div className="source-eyebrow">Saved investigation / frozen Python API</div><h2>{record.subjectLabel}</h2>
          <p>Parcel {record.subjectPin??'unresolved'} · {record.analysisDate}</p></div>
        <div><b data-testid="buyer-count">{record.selectedCount} eligible sale{record.selectedCount===1?'':'s'}</b>
          <small data-testid="buyer-status">{statusLabel(record.status)}</small></div></div>
        <div className="hpi-dossier-summary" data-testid="dossier-summary">
          <div><small>BUYER-REPORTED ASKING</small><strong>{record.askingPriceText}</strong></div>
          <div><small>BUYER-REPORTED AREA</small><strong>{record.buildingAreaText}</strong></div>
          <div><small>EVIDENCE QUALITY</small><strong>{statusLabel(record.status)}</strong></div>
          <div><small>CURRENT VALUATION</small><strong>Not produced</strong></div>
        </div>
        <div className="hpi-dossier-actions"><ActionButton type="button" onClick={()=>navigate('compare')} data-testid="dossier-compare" icon="compare" variant="secondary">Continue to comparison</ActionButton></div>
        <div className="buyer-result-grid"><article className="buyer-sale-pane"><div className="source-panel-head"><strong>Completed sale evidence</strong><small>ORIGINAL SERVER ORDER</small></div>
          {record.comparables.length? <div className="source-sale-list" data-testid="buyer-sales">
            {record.comparables.map(s=><button key={s.uiKey} type="button" data-testid="buyer-sale"
              aria-pressed={activeRank===s.rank} onClick={()=>setActiveRank(s.rank)}>
              <span className="source-sale-rank">{String(s.rank).padStart(2,'0')}</span>
              <span className="source-sale-main"><strong>{s.sameNeighbourhood?'Same neighbourhood':'Spatial evidence'}</strong><small>{s.saleDate} · Parcel {s.pin}</small>
              <span className="pi-sale-facts"><span>{s.areaDifferencePct}% area difference</span><span>{s.ageDays} days earlier</span></span></span>
              <span className="source-sale-price">{s.priceText}<small>Earlier completed sale</small></span>
            </button>)}</div>:<div className="source-empty" data-testid="buyer-insufficient"><Icon name="warning" size={32}/>
              <h3>Not enough eligible earlier sales</h3><p>No sale-based valuation can be inferred from this result.</p>
              <small>Backend reason: {record.reason??'Not available'}</small></div>}
          <div className="source-sale-detail" role="status" aria-live="polite"><small>SERVER MATCHING EXPLANATION</small>
            <p data-testid="buyer-explanation">{selected?selected.explanation:record.comparables.length
              ?'Choose a sale to inspect its exact original matching explanation.'
              :'No qualified comparable sales were returned by the Python matcher.'}</p>{selected&&<dl className="pi-evidence-detail" data-testid="sale-evidence-detail"><div><dt>Recorded document</dt><dd>{selected.document}</dd></div><div><dt>Earlier sale</dt><dd>{selected.saleDate}</dd></div><div><dt>Area difference</dt><dd>{selected.areaDifferencePct}%</dd></div><div><dt>Age at analysis</dt><dd>{selected.ageDays} days</dd></div></dl>}</div>{selected&&<EvidenceProfile facts={selected}/>}</article>
          {view==='investigate'&&<GeoMapPanel key={record.investigationId} record={record} selected={activeRank} onSelect={setActiveRank}/>}</div>
        <details className="hpi-provenance" open><summary>Source record and investigation details</summary><div className="buyer-provenance"><div><small>Investigation ID</small><strong data-testid="buyer-saved-id">{record.investigationId}</strong></div>
          <div><small>User-reported asking price</small><strong>{record.askingPriceText}</strong></div>
          <div><small>Fixture build</small><strong data-testid="buyer-build">{record.sourceBuildId}</strong></div>
          <div><small>Frozen snapshots</small><strong data-testid="buyer-snapshots">{record.sourceSnapshotIds.join(', ')}</strong></div>
          <div><small>Valuation</small><strong>Not produced</strong></div></div>
          <p data-testid="buyer-build-time">Fixture build timestamp: {record.sourceBuiltAtUtc} (not a source publication date).</p><p>Matching tier: {record.tier} · Building identity unverified · Historical source availability not established</p><p>All displayed sales are invented. No publisher property records or current market valuations are shown.</p></details>
        <BuyerEvidencePreview key={record.investigationId} record={record}/>
        {record.warnings.map((w,i)=><p key={i} className="buyer-warning">{w}</p>)}
      </section>}
      </section>
      <section hidden={view!=='compare'} className="hpi-view" aria-label="Compare">
        <div className="hpi-page-heading"><div><p className="hpi-eyebrow">PROPERTY DECISION WORKSPACE</p><h1>Compare the evidence.</h1><p>Preserve independent evidence and your own research notes.</p></div>
          <ActionButton type="button" className="hpi-primary" onClick={()=>navigate('saved')} icon="saved" variant="primary">Find saved properties</ActionButton></div>
        <SavedComparison active={record}/>
      </section>
      <footer className="source-footer"><b>HOUSE PRICE INTELLIGENCE / BUYER WORKSPACE</b>
        <span>Fictional · Loopback only · Exact cents · No real geographic map</span></footer>
      </main>
    </div>
  </div>;
}
