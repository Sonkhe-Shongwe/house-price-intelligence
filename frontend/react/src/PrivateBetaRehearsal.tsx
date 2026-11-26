/** Explicit fixture-only historical-shape view within the existing React bundle. */
import {useEffect,useRef,useState} from 'react';
import WorkspaceNavigation,{type WorkspaceView} from './WorkspaceNavigation';
import {privateBuyerService as service} from './privateBuyerService';
import {UUID,type Result,type Entry,type Comparison,type Workspace} from './privateBuyerContract';
import {formatExactUsd} from './evidenceBridge';
import EvidenceProfile from './EvidenceProfile';
import ComparisonMatrix from './ComparisonMatrix';
import './buyerWorkflow.css';
import './privateWorkspace.css';
function statusText(s:string){return ({supported_neighbourhood:'Neighbourhood evidence',exploratory_spatial:'Exploratory evidence',insufficient_data:'Insufficient evidence',out_of_coverage:'Outside coverage'} as Record<string,string>)[s]??s;}
/** Existing timestamps only; do not derive an address or expose a recovery ID. */
function savedTime(value:string){
  const time=Date.parse(value);
  if(!Number.isFinite(time))return 'Save time unavailable';
  return new Intl.DateTimeFormat('en-GB',{timeZone:'UTC',year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(time)+' UTC';
}
/** Read-only dossier. No map or subject identity is inferred from redacted evidence. */
function privateComparisonRows(entries:Entry[]){
  const values=(fn:(e:Entry)=>import('react').ReactNode)=>entries.map(fn);
  return [
    {label:'Buyer-reported asking price',kind:'money' as const,values:values(e=>e.investigation.asking_price_usd===null?'Not supplied':formatExactUsd(e.investigation.asking_price_usd))},
    {label:'Buyer-reported area',values:values(e=>e.investigation.buyer_reported_area_sqft.toLocaleString('en-US')+' sq ft')},
    {label:'Evidence status',kind:'status' as const,values:values(e=><span data-evidence={e.investigation.status}>{e.investigation.status.replaceAll('_',' ')}</span>)},
    {label:'Eligible completed sales',kind:'count' as const,values:values(e=>e.investigation.selected_count)},
    {label:'Analysis date',values:values(e=>e.investigation.analysis_date)},
    {label:'Historical sales',values:values(e=>e.investigation.sales.length?e.investigation.sales.map(s=><div className="cm-sale" key={s.rank}><strong>{formatExactUsd(s.sale_price_usd)}</strong><small>{s.sale_date}</small></div>):'No eligible sales')},
    {label:'Buyer notes',values:values(e=><span className="cm-note">{e.note_text||'None'}</span>)},
    {label:'Valuation',values:values(()=> 'Not produced')},
  ];
}
function PrivateEvidence({result}:{result:Result}){
  const [rank,setRank]=useState(1);
  const selected=result.sales.find(s=>s.rank===rank);
  return <section className="pw-card pw-dossier" data-testid="beta-result" aria-label="Saved evidence">
    <div className="pw-dossier-heading"><div><div className="pw-kicker">FROZEN HISTORICAL INVESTIGATION</div><h2>Saved evidence</h2></div><div className="pw-evidence-state" data-status={result.status}><strong>{statusText(result.status)}</strong><span>{result.selected_count} eligible sales · {result.status.replaceAll('_',' ')} · {result.analysis_date}</span></div></div>
    <dl className="pw-dossier-facts"><div><dt>Buyer-reported asking price</dt><dd>{result.asking_price_usd===null?'Not supplied':formatExactUsd(result.asking_price_usd)}</dd></div><div><dt>Buyer-reported area</dt><dd>{result.buyer_reported_area_sqft.toLocaleString('en-US')} sq ft</dd></div></dl>
    {result.sales.length?<div className="pw-table-wrap pw-evidence-table" role="region" tabIndex={0} aria-label="Eligible sales table, scroll horizontally if needed"><table><caption>Eligible completed sales · ranked by evidence policy</caption><thead><tr><th scope="col">Rank</th><th scope="col">Sale price</th><th scope="col">Sale date</th><th scope="col">Assessed area</th><th scope="col">Age / area difference</th><th scope="col">Location evidence</th></tr></thead><tbody>{result.sales.map(s=><tr key={s.rank} data-testid="beta-sale" data-selected={rank===s.rank}><td><button type="button" className="pw-rank" aria-label={'Inspect comparable '+s.rank} aria-pressed={rank===s.rank} onClick={()=>setRank(s.rank)}>{s.rank}</button></td><td><strong>{formatExactUsd(s.sale_price_usd)}</strong></td><td>{s.sale_date}</td><td>{s.assessed_area_sqft} sq ft ({s.assessment_year})</td><td>{s.age_days} days · {s.area_difference_pct}%</td><td>{s.location_evidence.replaceAll('_',' ')}</td></tr>)}</tbody></table></div>:<p className="pw-notice">No eligible sales. The available evidence does not support a comparison with previous sales.</p>}
    {selected&&<EvidenceProfile facts={{rank:selected.rank,ageDays:selected.age_days,areaDifferencePct:selected.area_difference_pct}}/>}
    <div className="pw-notice" data-testid="beta-geometry-unavailable"><strong>Geographic evidence unavailable.</strong> No verified property coordinates or building identity are displayed.</div>
    <p className="pw-sub pw-dossier-limits">Fictional source-shaped evidence. Historical source availability and public display rights are unverified. Historical evidence is not a valuation.</p>
  </section>;
}
export default function PrivateBetaRehearsal(){
  const [address,setAddress]=useState('1 Fictional Court'),[date,setDate]=useState('2025-04-01');
  const [area,setArea]=useState('1600'),[price,setPrice]=useState('');
  const [token,setToken]=useState<string|null>(null),[status,setStatus]=useState('');
  const [result,setResult]=useState<Result|null>(null),[iid,setIid]=useState('');
  const [busy,setBusy]=useState(false),[error,setError]=useState(false);
  const [signedOut,setSignedOut]=useState(false),[logoutError,setLogoutError]=useState(false);
  const [entries,setEntries]=useState<Entry[]>([]),[label,setLabel]=useState('My fictional comparison');
  const [sid,setSid]=useState(''),[comparison,setComparison]=useState<Comparison|null>(null);
  const [workspace,setWorkspace]=useState<Workspace|null>(null);
  const [view,setView]=useState<WorkspaceView>('home');
  const [workspaceRevision,setWorkspaceRevision]=useState(0);
  const [workspaceLoading,setWorkspaceLoading]=useState(false),[workspaceError,setWorkspaceError]=useState(false);
  const content=useRef<HTMLElement|null>(null),previousView=useRef(view),locked=useRef(false);
  const libraryVisible=view==='home'||view==='saved';
  useEffect(()=>{
    if(previousView.current!==view){previousView.current=view;content.current?.focus({preventScroll:true});}
  },[view]);
  useEffect(()=>{
    if(!libraryVisible||signedOut)return;
    const controller=new AbortController();
    setWorkspace(null);setWorkspaceError(false);setWorkspaceLoading(true);
    void service.listWorkspace(controller.signal).then(workspace=>{
      if(!controller.signal.aborted)setWorkspace(workspace);
    }).catch(()=>{if(!controller.signal.aborted)setWorkspaceError(true);}).finally(()=>{
      if(!controller.signal.aborted)setWorkspaceLoading(false);
    });
    return ()=>controller.abort();
  },[libraryVisible,signedOut,workspaceRevision]);
  function navigate(next:WorkspaceView){if(!locked.current){setError(false);setView(next);}}
  async function run(action:()=>Promise<void>){
    if(locked.current)return;locked.current=true;setBusy(true);setError(false);
    try{await action();}catch{setError(true);}finally{locked.current=false;setBusy(false);}
  }
  function clear(){setToken(null);setStatus('');setResult(null);}
  async function signOut(){
    if(locked.current)return;locked.current=true;setBusy(true);setLogoutError(false);
    try{
      await service.signOut();
      // No buyer data or draft notes remain in the signed-out view. Saved records stay on the server.
      clear();setAddress('');setDate('');setArea('');setPrice('');setIid('');setEntries([]);
      setLabel('');setSid('');setComparison(null);setWorkspace(null);setError(false);setSignedOut(true);
    }catch{setLogoutError(true);}finally{locked.current=false;setBusy(false);}
  }
  if(signedOut)return <main className="pw-signed-out"><div className="pw-brand-mark">HPI</div><h1>Signed out</h1><p role="status">Your session has ended. Saved investigations and comparisons remain available after signing in again.</p><a href="/">Return to sign in</a></main>;
  return <div className="pw-shell"><header className="pw-top"><div className="pw-brand"><span className="pw-brand-mark">HPI</span><div><strong>House Price Intelligence</strong><small>BUYER WORKSPACE</small></div></div><span className="pw-mode">Fictional data · Private</span><button className="pw-secondary" type="button" disabled={busy} data-testid="beta-sign-out" onClick={()=>void signOut()}>Sign out</button></header>
    <a className="hpi-skip" href="#pw-content">Skip to content</a><div className="pw-layout"><aside className="pw-side"><p>WORKSPACE</p><WorkspaceNavigation view={view} onNavigate={navigate} disabled={busy} prefix="beta-nav" label="Workspace navigation"/><div className="pw-side-note"><strong>Evidence, not estimates</strong><p>Historical sale records support investigation, not a current market valuation.</p></div></aside>
    <main id="pw-content" ref={content} tabIndex={-1} className="pw-main">
      <div className="pw-mode-banner" role="note">Private fictional workspace · Historical evidence only · No current valuation</div>
      {logoutError&&<p role="alert">Sign out could not be confirmed. Retry before leaving this session unattended.</p>}
      {error&&<p role="alert" data-testid="beta-error">Investigation unavailable. Check your session and input.</p>}
      {busy&&<p className="pw-sub" role="status">Working on your request…</p>}
      <section className="pw-view" hidden={view!=='investigate'} aria-label="Investigate">
      <div className="pw-intro" id="pw-investigate"><span className="pw-kicker">PROPERTY INTELLIGENCE / PRIVATE PILOT</span><h1>Investigate historical evidence</h1><p>Search a fictional parcel, review the evidence and build a shortlist you can revisit.</p><div className="pw-notice">Invented source-shaped records only. No real property records, valuation, building identity or geographic position.</div></div>
      <section className="pw-card"><h2>Find a property</h2><p className="pw-sub">Start with an address and the date of your investigation.</p><fieldset disabled={busy}>
        <legend className="pw-sr">Resolve a fictional property</legend><div className="pw-fields"><div>
        <label htmlFor="beta-address">Address</label><input id="beta-address" value={address} onChange={e=>{setAddress(e.target.value);clear();}}/></div><div>
        <label htmlFor="beta-date">Analysis date</label><input id="beta-date" type="date" value={date} onChange={e=>{setDate(e.target.value);clear();}}/></div></div>
        <button className="buyer-save" type="button" data-testid="beta-search" onClick={()=>void run(async()=>{
          clear();const m=await service.search(address,date);
          if(m.status==='one_eligible_candidate'){
            setToken(m.addressId);setStatus('One eligible parcel candidate');
          }else if(m.status==='ambiguous'||m.status==='no_match'){setStatus('No unique eligible candidate');}
          else throw Error('Unavailable');
        })}>Search</button><p role="status" data-testid="beta-match">{status}</p>
        <div className="pw-fields"><div><label htmlFor="beta-area">Buyer-reported area (sq ft)</label><input id="beta-area" type="number" min="1" value={area} onChange={e=>setArea(e.target.value)}/></div><div><label htmlFor="beta-price">Asking price (USD, optional)</label><input id="beta-price" value={price} onChange={e=>setPrice(e.target.value)}/></div></div>
        <button className="buyer-save" type="button" disabled={!token} data-testid="beta-create" onClick={()=>void run(async()=>{
          if(!token)throw Error('Unavailable');setResult(null);const r=await service.createInvestigation({addressId:token,analysisDate:date,area:Number(area),askingPrice:price||null});setResult(r);setIid(r.investigation_id);setWorkspace(null);
        })}>Save investigation</button>
        <div className="pw-recovery"><span>Advanced recovery</span><label htmlFor="beta-iid">Saved investigation ID</label><input id="beta-iid" data-testid="beta-id" value={iid} onChange={e=>setIid(e.target.value)}/>
        <button className="buyer-save" type="button" disabled={!UUID.test(iid)} data-testid="beta-reopen" onClick={()=>void run(async()=>{clear();setResult(await service.reopenInvestigation(iid));})}>Reopen saved investigation</button></div>
      </fieldset></section>
      {result&&<><PrivateEvidence key={result.investigation_id} result={result}/><div className="pw-dossier-actions"><button className="pw-secondary" type="button" data-testid="beta-add-comparison" disabled={busy||entries.length>=3||entries.some(e=>e.investigation_id===result.investigation_id)} onClick={()=>{setEntries(old=>[...old,{investigation_id:result.investigation_id,note_text:'',investigation:result}]);navigate('compare');}}>Add to comparison</button><button className="pw-secondary" type="button" disabled={busy} onClick={()=>navigate('compare')}>Open comparison ({entries.length})</button></div></>}
      </section>
      <section className="pw-view" hidden={!libraryVisible} aria-label="Saved workspace">
      <div className="pw-intro pw-home-heading"><div><span className="pw-kicker">RESEARCH WORKSPACE / PRIVATE PILOT</span><h1>{view==='home'?'A clearer view of property.':'Saved properties.'}</h1><p>Return to frozen historical investigations and compare your options on your own terms.</p></div><button className="pw-primary" type="button" data-testid="beta-new-investigation" disabled={busy} onClick={()=>navigate('investigate')}>New investigation</button></div>
      {view==='home'&&<div className="pw-editorial"><div><span className="pw-kicker">FIELD GUIDE / 01</span><h2>Evidence, not estimates.</h2><p>Historical completed sales can inform a decision. They do not establish a current property value.</p><button type="button" className="pw-secondary" disabled={busy} onClick={()=>navigate('methodology')}>Read methodology</button></div><div className="pw-editorial-mark" aria-hidden="true">H<span>/</span></div></div>}
      <div className="pw-card"><div className="pw-card-head"><div><h2>{view==='home'?'Recent research':'Your research library'}</h2><p className="pw-sub">Open records by date and evidence status. Saved addresses are not exposed by this service.</p></div><button className="pw-secondary" data-testid="beta-load-workspace" disabled={busy||workspaceLoading} onClick={()=>setWorkspaceRevision(n=>n+1)}>Refresh records</button></div>
      {workspaceLoading&&<p role="status">Loading saved records…</p>}
      {workspaceError&&<p role="alert">Saved records could not be verified. Refresh to retry.</p>}
      {workspace&&<div className="pw-saved-grid" data-testid="beta-workspace"><div><h3>Investigations</h3>{workspace.investigations.length===0?<p className="pw-sub">No saved investigations.</p>:workspace.investigations.map(i=><div className="pw-list-row" key={i.investigation_id}><div><strong>{statusText(i.status)}</strong><small>Analysis {i.analysis_date} · Saved {savedTime(i.created_at_utc)}</small></div><button className="pw-secondary" data-testid="beta-workspace-investigation" disabled={busy} onClick={()=>void run(async()=>{clear();const v=await service.reopenInvestigation(i.investigation_id);setResult(v);setIid(v.investigation_id);setView('investigate');})}>Open</button></div>)}</div><div><h3>Comparisons</h3>{workspace.comparisons.length===0?<p className="pw-sub">No saved comparisons.</p>:workspace.comparisons.map(i=><div className="pw-list-row" key={i.shortlist_id}><div><strong>{i.label}</strong><small>Saved {savedTime(i.created_at_utc)}</small></div><button className="pw-secondary" data-testid="beta-workspace-comparison" disabled={busy} onClick={()=>void run(async()=>{setComparison(null);const v=await service.reopenComparison(i.shortlist_id);setComparison(v);setSid(v.shortlist_id);setView('compare');})}>Open</button></div>)}</div>{workspace.truncated&&<p className="pw-sub">Showing the most recent 50 records per category.</p>}</div>}</div></section>
      <section className="pw-view" hidden={view!=='compare'} aria-label="Compare"><div className="pw-intro"><span className="pw-kicker">COMPARISON STUDIO</span><h1>Compare with context.</h1><p>Choose two or three saved investigations, preserve notes and compare the evidence.</p><button className="pw-secondary" type="button" disabled={busy} onClick={()=>navigate('saved')}>Find saved properties</button></div><div className="pw-card" id="pw-compare" aria-label="Saved property comparison">
        <h2>Comparison draft</h2>
        <fieldset disabled={busy}>
          <legend>Choose two or three distinct fictional parcels</legend>
          <p className="pw-sub">{entries.length} / 3 properties selected. Add from an open investigation.</p>
          {entries.length===0&&<p className="pw-notice">Open a saved investigation and add it to this draft. Choose at least two properties to save a comparison.</p>}
          <div className="pw-compare-draft" data-count={entries.length}>{entries.map((entry,i)=><article className="pw-compare-property" key={entry.investigation_id}>
            <div className="pw-kicker">PROPERTY {String(i+1).padStart(2,'0')}</div>
            <h3>{statusText(entry.investigation.status)}</h3>
            <strong className="pw-draft-money">{entry.investigation.asking_price_usd===null?'Not supplied':formatExactUsd(entry.investigation.asking_price_usd)}</strong>
            <small>Buyer-reported asking price</small>
            <p>{entry.investigation.analysis_date} · {entry.investigation.selected_count} eligible sales</p>
            <label htmlFor={'beta-note-'+i}>Property {i+1} note</label>
            <textarea id={'beta-note-'+i} rows={3} maxLength={800} value={entry.note_text} onChange={e=>setEntries(old=>old.map((x,j)=>j===i?{...x,note_text:e.target.value}:x))}/>
            <button type="button" className="pw-secondary" onClick={()=>setEntries(old=>old.filter(x=>x.investigation_id!==entry.investigation_id))}>Remove property {i+1}</button>
          </article>)}</div>
          <label htmlFor="beta-comparison-label">Comparison name</label><input id="beta-comparison-label" maxLength={80} value={label} onChange={e=>setLabel(e.target.value)}/>
          <button type="button" className="buyer-save" data-testid="beta-save-comparison" disabled={entries.length<2||!label.trim()} onClick={()=>void run(async()=>{
            setComparison(null);const c=await service.createComparison(label,entries);setComparison(c);setSid(c.shortlist_id);setWorkspace(null);
          })}>Save comparison</button>
          <div className="pw-recovery"><span>Advanced recovery</span><label htmlFor="beta-comparison-id">Saved comparison ID</label><input id="beta-comparison-id" data-testid="beta-comparison-id" value={sid} onChange={e=>setSid(e.target.value)}/>
          <button type="button" className="buyer-save" data-testid="beta-reopen-comparison" disabled={!UUID.test(sid)} onClick={()=>void run(async()=>{
            setComparison(null);setComparison(await service.reopenComparison(sid));
          })}>Reopen comparison</button></div>
        </fieldset>
        {comparison&&<section className="pw-frozen-comparison" data-testid="beta-comparison" aria-label="Frozen saved comparison">
          <div className="pw-kicker">SAVED SNAPSHOT / READ ONLY</div><h3>{comparison.label}</h3>
          <p className="pw-sub">This saved comparison is independent of the draft above. Notes and evidence shown here are the last server-confirmed snapshot. To save different notes, create a new comparison.</p>
          <ComparisonMatrix columns={comparison.entries.map((e,i)=>({key:e.investigation_id,title:'Property '+(i+1)}))} rows={privateComparisonRows(comparison.entries)} caption="Frozen historical evidence, not a valuation"/>
        </section>}
      </div></section>
      <section className="pw-view" hidden={view!=='methodology'} aria-label="Methodology"><div className="pw-intro"><span className="pw-kicker">FIELD GUIDE</span><h1>Evidence has limits.</h1><p>Understand what the private fictional service does and does not establish.</p></div><div className="pw-card"><h2>Historical evidence</h2><p>Earlier completed sales are not asking prices or current valuations. The service preserves its original ranked evidence when an investigation is reopened.</p><h2>Geographic coverage</h2><p>Property coordinates and building identity are withheld. An insufficient-evidence outcome is a valid result.</p><h2>Source and privacy</h2><p>Invented source-shaped records only. Historical availability and public display rights are unverified. Saved records belong to the authenticated workspace. Do not enter real personal information.</p></div></section>
    </main></div></div>;
}
