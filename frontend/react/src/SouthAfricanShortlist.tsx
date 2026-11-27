import {useEffect,useRef,useState} from 'react';
import {ActionButton,EmptyState,ScrollRegion,StatusMessage} from './UI';
import {decodeShortlist,formatZar,SHORTLIST_PATH,type Saved} from './saInvestigationContract';

export default function SouthAfricanShortlist({saved,disabled}:{saved:Saved[];disabled:boolean}){
  const [rows,setRows]=useState<Saved[]|null>(null),[selected,setSelected]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState('');
  const flight=useRef<AbortController|null>(null);
  async function read(signal:AbortSignal){
    const response=await fetch(SHORTLIST_PATH,{credentials:'same-origin',cache:'no-store',redirect:'error',signal});
    if(!response.ok||response.headers.get('X-Synthetic-Only')!=='true')throw Error('Shortlist unavailable');
    return decodeShortlist(await response.json());
  }
  async function refresh(){
    if(flight.current)return;
    const controller=new AbortController();flight.current=controller;setBusy(true);setNotice('');
    try{setRows(await read(controller.signal));}catch{if(!controller.signal.aborted){setRows(null);setNotice('Shortlist unavailable. Refresh to try again.');}}
    finally{if(flight.current===controller){flight.current=null;if(!controller.signal.aborted)setBusy(false);}}
  }
  useEffect(()=>{void refresh();return()=>{flight.current?.abort();flight.current=null;};},[]);
  async function mutate(action:'add'|'remove',id:string){
    if(flight.current||rows===null||disabled||!id)return;
    const controller=new AbortController();flight.current=controller;setBusy(true);setNotice('');
    try{
      const res=await fetch(SHORTLIST_PATH,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,investigation_id:id}),credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal});
      if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('Not confirmed');
      const next=decodeShortlist(await res.json());
      if(next.some(r=>r.investigation_id===id)!==(action==='add'))throw Error('Membership mismatch');
      setRows(next);setNotice(action==='add'?'Property shortlisted.':'Property removed.');
    }catch{
      if(!controller.signal.aborted){
        try{setRows(await read(controller.signal));setNotice('Change response not confirmed. Current server shortlist refreshed; check membership before retrying.');}
        catch{if(!controller.signal.aborted){setRows(null);setNotice('Shortlist unavailable. Refresh before retrying.');}}
      }
    }finally{if(flight.current===controller){flight.current=null;if(!controller.signal.aborted)setBusy(false);}}
  }
  const picked=saved.find(r=>r.investigation_id===selected);
  const duplicate=!!picked&&!!rows?.some(r=>r.request.subject_key.value===picked.request.subject_key.value);
  const locked=disabled||busy||rows===null;
  return <section className="za-panel za-method" aria-labelledby="za-shortlist-heading" aria-busy={busy} data-testid="za-shortlist">
    <h2 id="za-shortlist-heading">Shortlist and compare</h2>
    <p className="za-muted">Choose two or three distinct saved fictional properties. Membership lasts only for this local server session. Evidence is frozen, not recalculated. No valuation or recommendation.</p>
    <label htmlFor="za-shortlist-select">Saved investigation to shortlist</label>
    <select id="za-shortlist-select" className="hpi-field" value={picked?selected:''} disabled={locked} onChange={e=>setSelected(e.target.value)}>
      <option value="">Choose a saved investigation</option>
      {saved.map(r=><option key={r.investigation_id} value={r.investigation_id}>Erf {r.request.subject_key.value.slice(-6)} · {r.request.analysis_date} · {r.evidence.subject.asking_price?formatZar(r.evidence.subject.asking_price):'No asking price'}</option>)}
    </select>
    <ActionButton variant="primary" disabled={locked||!picked||duplicate||(rows?.length??0)>=3} onClick={()=>void mutate('add',selected)} data-testid="za-shortlist-add">Add to shortlist</ActionButton>{' '}
    <ActionButton disabled={busy||disabled} onClick={()=>void refresh()}>Refresh shortlist</ActionButton>
    {duplicate&&<p className="za-muted">This fictional parcel is already shortlisted.</p>}
    {rows?.length===3&&<p className="za-muted">Three-property limit reached. Remove a property before adding another.</p>}
    {notice&&<StatusMessage>{notice}</StatusMessage>}
    {rows===null?<EmptyState>Shortlist not available.</EmptyState>:<>
      <p data-testid="za-shortlist-count">{rows.length} of 3 properties</p>
      {rows.map(row=><div key={row.investigation_id} className="za-history-item" data-testid="za-shortlist-member"><strong>Erf {row.request.subject_key.value.slice(-6)}</strong><ActionButton disabled={locked} aria-label={'Remove '+row.investigation_id} onClick={()=>void mutate('remove',row.investigation_id)}>Remove</ActionButton></div>)}
      {rows.length<2?<EmptyState>Add at least two distinct properties to compare frozen evidence.</EmptyState>:
      <ScrollRegion label="Fictional property comparison" className="za-table-scroll"><table data-testid="za-comparison"><caption>Frozen fictional property comparison · no estimated value</caption>
        <thead><tr><th scope="col">Evidence</th>{rows.map(r=><th scope="col" key={r.investigation_id}>Erf {r.request.subject_key.value.slice(-6)}</th>)}</tr></thead>
        <tbody>
          <tr><th scope="row">User-reported asking price</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.subject.asking_price?formatZar(r.evidence.subject.asking_price):'Not provided'}</td>)}</tr>
          <tr><th scope="row">Analysis date / mode</th>{rows.map(r=><td key={r.investigation_id}>{r.request.analysis_date} · {r.request.mode==='as_of'?'Fictional as-of':'Retrospective'}</td>)}</tr>
          <tr><th scope="row">Dwelling / land (m²)</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.subject.dwelling_extent??'Unknown'} / {r.evidence.subject.land_extent??'Unknown'}</td>)}</tr>
          <tr><th scope="row">Comparable evidence</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.status==='fictional_supported'?r.evidence.selected_count+' fictional sales · '+r.evidence.window_days+' days':'Insufficient or unsupported evidence'}</td>)}</tr>
          <tr><th scope="row">Invented registered-sale consideration</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.comparables.length?r.evidence.comparables.map(s=><div key={s.event_id}>{s.reported_sale_date} · {formatZar(s.sale_consideration)}</div>):'No comparable sale amounts'}</td>)}</tr>
        </tbody></table></ScrollRegion>}
    </>}
  </section>;
}
