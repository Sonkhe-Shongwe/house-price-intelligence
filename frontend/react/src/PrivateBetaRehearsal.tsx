/** Explicit fixture-only historical-shape view within the existing React bundle. */
import {useState} from 'react';
import {fixtureFetch} from './fixtureFetch';
import {formatExactUsd} from './evidenceBridge';
import './buyerWorkflow.css';
import './privateWorkspace.css';
const ROOT='/v1/private-beta-rehearsal';
type Sale={rank:number;sale_date:string;sale_price_usd:string;assessment_year:number;assessed_area_sqft:number;area_difference_pct:number;age_days:number;location_evidence:string};
type Result={investigation_id:string;status:string;analysis_date:string;selected_count:number;sales:Sale[];asking_price_usd:string|null};
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
function record(x:unknown):Record<string,unknown>{
  if(!x||typeof x!=='object'||Array.isArray(x))throw Error('Unavailable');
  return x as Record<string,unknown>;
}
function exact(r:Record<string,unknown>,keys:string){
  if(Object.keys(r).sort().join(' ')!==keys.split(' ').sort().join(' '))throw Error('Unavailable');
}
function decode(x:unknown):Result{
  const r=record(x);
  exact(r,'investigation_id contract_version source_kind status tier analysis_date selected_count sales asking_price_usd asking_price_source buyer_reported_area_sqft provenance building_identity_verified geometry_available valuation');
  const p=record(r.provenance);
  exact(p,'publisher_attributed build_revision retrieved_at_utc historical_asof_verified public_display_approved');
  if(r.contract_version!=='historical-beta-evidence-v1'||r.source_kind!=='historical_shape_rehearsal'
    ||typeof r.investigation_id!=='string'||!UUID.test(r.investigation_id)
    ||r.valuation!==null||r.geometry_available!==false||r.building_identity_verified!==false
    ||p.publisher_attributed!==false||p.historical_asof_verified!==false||p.public_display_approved!==false
    ||r.asking_price_source!=='buyer_reported'||typeof r.analysis_date!=='string'
    ||!['supported_neighbourhood','exploratory_spatial','insufficient_data','out_of_coverage'].includes(String(r.status))
    ||!Array.isArray(r.sales)||r.sales.length!==r.selected_count||r.sales.length>5
    ||(r.asking_price_usd!==null&&(typeof r.asking_price_usd!=='string'||!/^[0-9]+\.[0-9]{2}$/.test(r.asking_price_usd))))throw Error('Unavailable');
  for(const [i,item] of r.sales.entries()){
    const s=record(item);
    exact(s,'rank sale_date sale_price_usd assessment_year assessed_area_sqft area_difference_pct age_days location_evidence');
    if(s.rank!==i+1||typeof s.sale_price_usd!=='string'||!/^[0-9]+\.[0-9]{2}$/.test(s.sale_price_usd)
       ||typeof s.sale_date!=='string'||typeof s.assessed_area_sqft!=='number'||typeof s.assessment_year!=='number'
       ||typeof s.age_days!=='number'||typeof s.area_difference_pct!=='number'
       ||!['same_neighbourhood','exploratory_spatial'].includes(String(s.location_evidence)))throw Error('Unavailable');
  }
  return r as unknown as Result;
}
type Entry={investigation_id:string;note_text:string;investigation:Result};
type Comparison={shortlist_id:string;label:string;entries:Entry[]};
function decodeComparison(x:unknown):Comparison{
  const r=record(x);
  exact(r,'source_kind shortlist_id label created_at_utc entries');
  if(r.source_kind!=='historical_shape_rehearsal'||typeof r.shortlist_id!=='string'||!UUID.test(r.shortlist_id)
    ||typeof r.label!=='string'||typeof r.created_at_utc!=='string'||!Array.isArray(r.entries)
    ||r.entries.length<2||r.entries.length>3)throw Error('Unavailable');
  const entries=r.entries.map(x=>{
    const e=record(x);exact(e,'investigation_id note_text investigation');
    const investigation=decode(e.investigation);
    if(e.investigation_id!==investigation.investigation_id||typeof e.note_text!=='string'||e.note_text.length>800)throw Error('Unavailable');
    return {investigation_id:investigation.investigation_id,note_text:e.note_text,investigation};
  });
  if(new Set(entries.map(e=>e.investigation_id)).size!==entries.length)throw Error('Unavailable');
  return {shortlist_id:r.shortlist_id,label:r.label,entries};
}
type SavedInvestigation={investigation_id:string;analysis_date:string;status:string;created_at_utc:string};
type SavedShortlist={shortlist_id:string;label:string;created_at_utc:string};
type Workspace={investigations:SavedInvestigation[];comparisons:SavedShortlist[];truncated:boolean};
function decodeWorkspace(x:unknown):Workspace{
  const r=record(x);exact(r,'source_kind investigations comparisons truncated');
  if(r.source_kind!=='historical_shape_rehearsal'||!Array.isArray(r.investigations)||!Array.isArray(r.comparisons)||r.investigations.length>50||r.comparisons.length>50||typeof r.truncated!=='boolean')throw Error('Unavailable');
  const investigations=r.investigations.map(x=>{const i=record(x);exact(i,'investigation_id analysis_date status created_at_utc');
    if(typeof i.investigation_id!=='string'||!UUID.test(i.investigation_id)||typeof i.analysis_date!=='string'||typeof i.created_at_utc!=='string'||!['supported_neighbourhood','exploratory_spatial','insufficient_data','out_of_coverage'].includes(String(i.status)))throw Error('Unavailable');
    return i as unknown as SavedInvestigation;});
  const comparisons=r.comparisons.map(x=>{const i=record(x);exact(i,'shortlist_id label created_at_utc');
    if(typeof i.shortlist_id!=='string'||!UUID.test(i.shortlist_id)||typeof i.label!=='string'||i.label.length>80||typeof i.created_at_utc!=='string')throw Error('Unavailable');
    return i as unknown as SavedShortlist;});
  return {investigations,comparisons,truncated:r.truncated};
}
function statusText(s:string){return ({supported_neighbourhood:'Neighbourhood evidence',exploratory_spatial:'Exploratory evidence',insufficient_data:'Insufficient evidence',out_of_coverage:'Outside coverage'} as Record<string,string>)[s]??s;}
async function api(path:string,body?:unknown){
  const res=await fixtureFetch(ROOT+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!res.ok)throw Error('Unavailable');
  return await res.json() as unknown;
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
  async function run(action:()=>Promise<void>){
    setBusy(true);setError(false);
    try{await action();}catch{setError(true);}finally{setBusy(false);}
  }
  function clear(){setToken(null);setStatus('');setResult(null);}
  async function signOut(){
    setBusy(true);setLogoutError(false);
    try{
      const response=await fixtureFetch('/auth/logout',{method:'POST'});
      if(!response.ok||record(await response.json()).logged_out!==true)throw Error('Sign out unavailable');
      // No buyer data or draft notes remain in the signed-out view. Saved records stay on the server.
      clear();setAddress('');setDate('');setArea('');setPrice('');setIid('');setEntries([]);
      setLabel('');setSid('');setComparison(null);setWorkspace(null);setError(false);setSignedOut(true);
    }catch{setLogoutError(true);}finally{setBusy(false);}
  }
  if(signedOut)return <main className="pw-signed-out"><div className="pw-brand-mark">HPI</div><h1>Signed out</h1><p role="status">Your session has ended. Saved investigations and comparisons remain available after signing in again.</p><a href="/">Return to sign in</a></main>;
  return <div className="pw-shell"><header className="pw-top"><div className="pw-brand"><span className="pw-brand-mark">HPI</span><div><strong>House Price Intelligence</strong><small>BUYER WORKSPACE</small></div></div><span className="pw-mode">Fictional data · Private</span><button className="pw-secondary" type="button" disabled={busy} data-testid="beta-sign-out" onClick={()=>void signOut()}>Sign out</button></header>
    <div className="pw-layout"><aside className="pw-side"><p>WORKSPACE</p><nav aria-label="Workspace navigation"><a href="#pw-investigate">01 &nbsp; Investigate</a><a href="#pw-saved">02 &nbsp; Saved workspace</a><a href="#pw-compare">03 &nbsp; Compare properties</a></nav><div className="pw-side-note"><strong>Evidence, not estimates</strong><p>Historical sale records support investigation, not a current market valuation.</p></div></aside>
    <main className="pw-main">
      <div className="pw-intro" id="pw-investigate"><span className="pw-kicker">PROPERTY INTELLIGENCE / PRIVATE PILOT</span><h1>Investigate historical evidence</h1><p>Search a fictional parcel, review the evidence and build a shortlist you can revisit.</p><div className="pw-notice">Invented source-shaped records only. No real property records, valuation, building identity or geographic position.</div></div>
      <section className="pw-card"><h2>Find a property</h2><p className="pw-sub">Start with an address and the date of your investigation.</p><fieldset disabled={busy}>
        <legend className="pw-sr">Resolve a fictional property</legend><div className="pw-fields"><div>
        <label htmlFor="beta-address">Address</label><input id="beta-address" value={address} onChange={e=>{setAddress(e.target.value);clear();}}/></div><div>
        <label htmlFor="beta-date">Analysis date</label><input id="beta-date" type="date" value={date} onChange={e=>{setDate(e.target.value);clear();}}/></div></div>
        <button className="buyer-save" type="button" data-testid="beta-search" onClick={()=>void run(async()=>{
          clear();const m=record(await api('/search',{query:address,analysis_date:date}));
          if(m.status==='one_eligible_candidate'&&typeof m.address_id==='string'&&/^[a-z0-9-]{1,40}$/.test(m.address_id)){
            setToken(m.address_id);setStatus('One eligible parcel candidate');
          }else if(m.status==='ambiguous'||m.status==='no_match'){setStatus('No unique eligible candidate');}
          else throw Error('Unavailable');
        })}>Search</button><p role="status" data-testid="beta-match">{status}</p>
        <div className="pw-fields"><div><label htmlFor="beta-area">Buyer-reported area (sq ft)</label><input id="beta-area" type="number" min="1" value={area} onChange={e=>setArea(e.target.value)}/></div><div><label htmlFor="beta-price">Asking price (USD, optional)</label><input id="beta-price" value={price} onChange={e=>setPrice(e.target.value)}/></div></div>
        <button className="buyer-save" type="button" disabled={!token} data-testid="beta-create" onClick={()=>void run(async()=>{
          setResult(null);const r=decode(await api('/investigations',{township_code:'17',class_code:'203',analysis_date:date,subject:{address_id:token,building_area_sqft:Number(area),asking_price_usd:price||null}}));setResult(r);setIid(r.investigation_id);setWorkspace(null);
        })}>Save investigation</button>
        <div className="pw-recovery"><span>Advanced recovery</span><label htmlFor="beta-iid">Saved investigation ID</label><input id="beta-iid" data-testid="beta-id" value={iid} onChange={e=>setIid(e.target.value)}/>
        <button className="buyer-save" type="button" disabled={!UUID.test(iid)} data-testid="beta-reopen" onClick={()=>void run(async()=>{setResult(null);setResult(decode(await api('/investigations/'+iid)));})}>Reopen saved investigation</button></div>
      </fieldset></section>
      {logoutError&&<p role="alert">Sign out could not be confirmed. Retry before leaving this session unattended.</p>}
      {error&&<p role="alert" data-testid="beta-error">Investigation unavailable. Check your session and input.</p>}
      {busy&&<p className="pw-sub" role="status">Working on your request…</p>}
      {result&&<section className="pw-card" data-testid="beta-result" aria-label="Saved evidence">
        <h2>Saved evidence</h2><p>{result.selected_count} eligible sales · {result.status.replaceAll('_',' ')} · {result.analysis_date}</p>
        <p>Buyer-reported asking price: {result.asking_price_usd===null?'Not supplied':formatExactUsd(result.asking_price_usd)}</p>
        {result.sales.length?<div className="pw-table-wrap"><table><caption>Eligible completed sales · ranked by evidence policy</caption><thead><tr><th>Rank</th><th>Sale price</th><th>Sale date</th><th>Assessed area</th><th>Age / area difference</th><th>Location evidence</th></tr></thead><tbody>{result.sales.map(s=><tr key={s.rank} data-testid="beta-sale"><td>{s.rank}</td><td><strong>{formatExactUsd(s.sale_price_usd)}</strong></td><td>{s.sale_date}</td><td>{s.assessed_area_sqft} sq ft ({s.assessment_year})</td><td>{s.age_days} days · {s.area_difference_pct}%</td><td>{s.location_evidence.replaceAll('_',' ')}</td></tr>)}</tbody></table></div>:<p className="pw-notice">No eligible sales. The available evidence does not support a comparison with previous sales.</p>}
        <p className="pw-sub">Historical evidence is not a valuation.</p>
      </section>}
      <section className="pw-card" id="pw-saved" aria-label="Saved workspace"><div className="pw-card-head"><div><h2>Saved workspace</h2><p className="pw-sub">Reopen your investigations and comparisons without entering an ID.</p></div><button className="pw-secondary" data-testid="beta-load-workspace" disabled={busy} onClick={()=>void run(async()=>{setWorkspace(decodeWorkspace(await api('/workspace')));})}>{workspace?'Refresh':'Load saved records'}</button></div>
      {workspace&&<div className="pw-saved-grid" data-testid="beta-workspace"><div><h3>Investigations</h3>{workspace.investigations.length===0?<p className="pw-sub">No saved investigations.</p>:workspace.investigations.map(i=><div className="pw-list-row" key={i.investigation_id}><div><strong>{statusText(i.status)}</strong><small>Analysis {i.analysis_date} · Saved {i.created_at_utc.slice(0,10)}</small></div><button className="pw-secondary" data-testid="beta-workspace-investigation" disabled={busy} onClick={()=>void run(async()=>{setResult(null);const v=decode(await api('/investigations/'+i.investigation_id));setResult(v);setIid(v.investigation_id);})}>Open</button></div>)}</div><div><h3>Comparisons</h3>{workspace.comparisons.length===0?<p className="pw-sub">No saved comparisons.</p>:workspace.comparisons.map(i=><div className="pw-list-row" key={i.shortlist_id}><div><strong>{i.label}</strong><small>Saved {i.created_at_utc.slice(0,10)}</small></div><button className="pw-secondary" data-testid="beta-workspace-comparison" disabled={busy} onClick={()=>void run(async()=>{setComparison(null);const v=decodeComparison(await api('/shortlists/'+i.shortlist_id));setComparison(v);setSid(v.shortlist_id);})}>Open</button></div>)}</div>{workspace.truncated&&<p className="pw-sub">Showing the most recent 50 records per category.</p>}</div>}</section>
      <section className="pw-card" id="pw-compare" aria-label="Saved property comparison">
        <h2>Compare saved investigations</h2>
        <fieldset disabled={busy}>
          <legend>Choose two or three distinct fictional parcels</legend>
          <button type="button" className="buyer-save" data-testid="beta-add-comparison" disabled={!result||entries.length>=3||entries.some(e=>e.investigation_id===result.investigation_id)} onClick={()=>{
            if(result)setEntries(old=>[...old,{investigation_id:result.investigation_id,note_text:'',investigation:result}]);
          }}>Add saved investigation</button>
          {entries.map((entry,i)=><div key={entry.investigation_id}>
            <p>Property {i+1}: {entry.investigation.analysis_date} · {entry.investigation.selected_count} eligible sales</p>
            <label htmlFor={'beta-note-'+i}>Property {i+1} note</label>
            <input id={'beta-note-'+i} maxLength={800} value={entry.note_text} onChange={e=>setEntries(old=>old.map((x,j)=>j===i?{...x,note_text:e.target.value}:x))}/>
            <button type="button" onClick={()=>setEntries(old=>old.filter(x=>x.investigation_id!==entry.investigation_id))}>Remove property {i+1}</button>
          </div>)}
          <label htmlFor="beta-comparison-label">Comparison name</label><input id="beta-comparison-label" maxLength={80} value={label} onChange={e=>setLabel(e.target.value)}/>
          <button type="button" className="buyer-save" data-testid="beta-save-comparison" disabled={entries.length<2||!label.trim()} onClick={()=>void run(async()=>{
            setComparison(null);const c=decodeComparison(await api('/shortlists',{label,entries:entries.map(({investigation_id,note_text})=>({investigation_id,note_text}))}));setComparison(c);setSid(c.shortlist_id);setWorkspace(null);
          })}>Save comparison</button>
          <div className="pw-recovery"><span>Advanced recovery</span><label htmlFor="beta-comparison-id">Saved comparison ID</label><input id="beta-comparison-id" data-testid="beta-comparison-id" value={sid} onChange={e=>setSid(e.target.value)}/>
          <button type="button" className="buyer-save" data-testid="beta-reopen-comparison" disabled={!UUID.test(sid)} onClick={()=>void run(async()=>{
            setComparison(null);setComparison(decodeComparison(await api('/shortlists/'+sid)));
          })}>Reopen comparison</button></div>
        </fieldset>
        {comparison&&<div data-testid="beta-comparison">
          <h3>{comparison.label}</h3>
          <div className="pw-table-wrap"><table><caption>Frozen historical evidence, not a valuation</caption><thead><tr><th scope="col">Evidence</th>{comparison.entries.map((e,i)=><th scope="col" key={e.investigation_id}>Property {i+1}</th>)}</tr></thead>
          <tbody>
            <tr><th scope="row">Analysis date</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.analysis_date}</td>)}</tr>
            <tr><th scope="row">Evidence status</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.status.replaceAll('_',' ')}</td>)}</tr>
            <tr><th scope="row">Buyer-reported asking price</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.asking_price_usd===null?'Not supplied':formatExactUsd(e.investigation.asking_price_usd)}</td>)}</tr>
            <tr><th scope="row">Historical sales</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.sales.map(s=><div key={s.rank}>{formatExactUsd(s.sale_price_usd)} · {s.sale_date}</div>)}</td>)}</tr>
            <tr><th scope="row">Buyer notes</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.note_text||'None'}</td>)}</tr>
          </tbody></table></div>
        </div>}
      </section>
    </main></div></div>;
}
