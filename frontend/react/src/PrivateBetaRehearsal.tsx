/** Explicit fixture-only historical-shape view within the existing React bundle. */
import {useState} from 'react';
import {fixtureFetch} from './fixtureFetch';
import {formatExactUsd} from './evidenceBridge';
import './buyerWorkflow.css';
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
  const [entries,setEntries]=useState<Entry[]>([]),[label,setLabel]=useState('My fictional comparison');
  const [sid,setSid]=useState(''),[comparison,setComparison]=useState<Comparison|null>(null);
  async function run(action:()=>Promise<void>){
    setBusy(true);setError(false);
    try{await action();}catch{setError(true);}finally{setBusy(false);}
  }
  function clear(){setToken(null);setStatus('');setResult(null);}
  return <><header className="app-topbar"><strong>House Price Intelligence</strong><span>Private investigation rehearsal</span></header>
    <main className="buyer-pane">
      <h1>Investigate historical evidence</h1>
      <p>Invented source-shaped records only. No real property records, valuation, building identity or geographic position.</p>
      <fieldset disabled={busy}>
        <legend>Resolve a fictional property</legend>
        <label htmlFor="beta-address">Address</label><input id="beta-address" value={address} onChange={e=>{setAddress(e.target.value);clear();}}/>
        <label htmlFor="beta-date">Analysis date</label><input id="beta-date" type="date" value={date} onChange={e=>{setDate(e.target.value);clear();}}/>
        <button className="buyer-save" type="button" data-testid="beta-search" onClick={()=>void run(async()=>{
          clear();const m=record(await api('/search',{query:address,analysis_date:date}));
          if(m.status==='one_eligible_candidate'&&typeof m.address_id==='string'&&/^[a-z0-9-]{1,40}$/.test(m.address_id)){
            setToken(m.address_id);setStatus('One eligible parcel candidate');
          }else if(m.status==='ambiguous'||m.status==='no_match'){setStatus('No unique eligible candidate');}
          else throw Error('Unavailable');
        })}>Search</button><p role="status" data-testid="beta-match">{status}</p>
        <label htmlFor="beta-area">Buyer-reported area (sq ft)</label><input id="beta-area" type="number" min="1" value={area} onChange={e=>setArea(e.target.value)}/>
        <label htmlFor="beta-price">Asking price (USD, optional)</label><input id="beta-price" value={price} onChange={e=>setPrice(e.target.value)}/>
        <button className="buyer-save" type="button" disabled={!token} data-testid="beta-create" onClick={()=>void run(async()=>{
          setResult(null);const r=decode(await api('/investigations',{township_code:'17',class_code:'203',analysis_date:date,subject:{address_id:token,building_area_sqft:Number(area),asking_price_usd:price||null}}));setResult(r);setIid(r.investigation_id);
        })}>Save investigation</button>
        <label htmlFor="beta-iid">Saved investigation ID</label><input id="beta-iid" data-testid="beta-id" value={iid} onChange={e=>setIid(e.target.value)}/>
        <button className="buyer-save" type="button" disabled={!UUID.test(iid)} data-testid="beta-reopen" onClick={()=>void run(async()=>{setResult(null);setResult(decode(await api('/investigations/'+iid)));})}>Reopen saved investigation</button>
      </fieldset>
      {error&&<p role="alert" data-testid="beta-error">Investigation unavailable. Check your session and input.</p>}
      {result&&<section className="hpi-provenance" data-testid="beta-result" aria-label="Saved evidence">
        <h2>Saved evidence</h2><p>{result.selected_count} eligible sales · {result.status.replaceAll('_',' ')} · {result.analysis_date}</p>
        <p>Buyer-reported asking price: {result.asking_price_usd===null?'Not supplied':formatExactUsd(result.asking_price_usd)}</p>
        <ol>{result.sales.map(s=><li key={s.rank} data-testid="beta-sale"><strong>{formatExactUsd(s.sale_price_usd)}</strong> · {s.sale_date} · {s.assessed_area_sqft} sq ft (assessment {s.assessment_year}) · {s.age_days} days earlier · {s.area_difference_pct}% area difference · {s.location_evidence.replaceAll('_',' ')}</li>)}</ol>
      </section>}
      <section className="hpi-provenance" aria-label="Saved property comparison">
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
            setComparison(null);const c=decodeComparison(await api('/shortlists',{label,entries:entries.map(({investigation_id,note_text})=>({investigation_id,note_text}))}));setComparison(c);setSid(c.shortlist_id);
          })}>Save comparison</button>
          <label htmlFor="beta-comparison-id">Saved comparison ID</label><input id="beta-comparison-id" data-testid="beta-comparison-id" value={sid} onChange={e=>setSid(e.target.value)}/>
          <button type="button" className="buyer-save" data-testid="beta-reopen-comparison" disabled={!UUID.test(sid)} onClick={()=>void run(async()=>{
            setComparison(null);setComparison(decodeComparison(await api('/shortlists/'+sid)));
          })}>Reopen comparison</button>
        </fieldset>
        {comparison&&<div data-testid="beta-comparison">
          <h3>{comparison.label}</h3>
          <table><caption>Frozen historical evidence, not a valuation</caption><thead><tr><th scope="col">Evidence</th>{comparison.entries.map((e,i)=><th scope="col" key={e.investigation_id}>Property {i+1}</th>)}</tr></thead>
          <tbody>
            <tr><th scope="row">Analysis date</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.analysis_date}</td>)}</tr>
            <tr><th scope="row">Evidence status</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.status.replaceAll('_',' ')}</td>)}</tr>
            <tr><th scope="row">Buyer-reported asking price</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.asking_price_usd===null?'Not supplied':formatExactUsd(e.investigation.asking_price_usd)}</td>)}</tr>
            <tr><th scope="row">Historical sales</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.investigation.sales.map(s=><div key={s.rank}>{formatExactUsd(s.sale_price_usd)} · {s.sale_date}</div>)}</td>)}</tr>
            <tr><th scope="row">Buyer notes</th>{comparison.entries.map(e=><td key={e.investigation_id}>{e.note_text||'None'}</td>)}</tr>
          </tbody></table>
        </div>}
      </section>
    </main></>;
}
