import {useEffect,useRef,useState} from 'react';
import {ActionButton,EmptyState,ScrollRegion,StatusMessage} from './UI';
import {evidenceExplanation,evidenceModeLimit} from './saEvidenceExplanation';
import {decodeShortlist,formatZar,SHORTLIST_PATH,validDecisionNote,type Saved,type ShortlistMember} from './saInvestigationContract';

export default function SouthAfricanShortlist({saved,disabled}:{saved:Saved[];disabled:boolean}){
  const [rows,setRows]=useState<ShortlistMember[]|null>(null),[selected,setSelected]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState('');
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
  async function mutate(action:'add'|'remove'|'note',id:string,note?:string){
    if(flight.current||rows===null||disabled||!id||(action==='note'&&!validDecisionNote(note)))return;
    const controller=new AbortController();flight.current=controller;setBusy(true);setNotice('');
    try{
      const res=await fetch(SHORTLIST_PATH,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(action==='note'?{action,investigation_id:id,note_text:note}:{action,investigation_id:id}),credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal});
      if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('Not confirmed');
      const next=decodeShortlist(await res.json());
      if(next.some(r=>r.investigation_id===id)!==(action!=='remove')||(action==='note'&&next.find(r=>r.investigation_id===id)?.note_text!==note))throw Error('Membership or note mismatch');
      setRows(next);setNotice(action==='add'?'Property shortlisted.':action==='remove'?'Property removed.':'Decision note saved.');
    }catch{
      if(!controller.signal.aborted){
        try{setRows(await read(controller.signal));setNotice('Change response not confirmed. Current server shortlist refreshed; check membership and saved notes before retrying.');}
        catch{if(!controller.signal.aborted){setRows(null);setNotice('Shortlist unavailable. Refresh before retrying.');}}
      }
    }finally{if(flight.current===controller){flight.current=null;if(!controller.signal.aborted)setBusy(false);}}
  }
  const picked=saved.find(r=>r.investigation_id===selected);
  const duplicate=!!picked&&!!rows?.some(r=>r.request.subject_key.value===picked.request.subject_key.value);
  const locked=disabled||busy||rows===null;
  return <section className="za-panel za-method" aria-labelledby="za-shortlist-heading" aria-busy={busy} data-testid="za-shortlist">
    <h2 id="za-shortlist-heading">Shortlist and compare</h2>
    <p className="za-muted">Choose two or three distinct saved fictional properties. Membership and notes are temporary; do not rely on recovery after ending the rehearsal. Use invented notes only; do not enter personal or real property information. Evidence is frozen, not recalculated. No valuation or recommendation.</p>
    <label htmlFor="za-shortlist-select">Saved investigation to shortlist</label>
    <select id="za-shortlist-select" className="hpi-field" value={picked?selected:''} disabled={locked} onChange={e=>setSelected(e.target.value)}>
      <option value="">Choose a saved investigation</option>
      {saved.map(r=><option key={r.investigation_id} value={r.investigation_id}>Erf {r.request.subject_key.value.slice(-6)} · {r.request.analysis_date} · {r.evidence.subject.asking_price?formatZar(r.evidence.subject.asking_price):'No asking price'}</option>)}
    </select>
    <ActionButton icon="plus" variant="primary" disabled={locked||!picked||duplicate||(rows?.length??0)>=3} onClick={()=>void mutate('add',selected)} data-testid="za-shortlist-add">Add to shortlist</ActionButton>{' '}
    <ActionButton icon="refresh" disabled={busy||disabled} onClick={()=>void refresh()}>Refresh shortlist</ActionButton>
    {duplicate&&<p className="za-muted">This fictional parcel is already shortlisted.</p>}
    {rows?.length===3&&<p className="za-muted">Three-property limit reached. Remove a property before adding another.</p>}
    {notice&&<StatusMessage>{notice}</StatusMessage>}
    {rows===null?<EmptyState>Shortlist not available.</EmptyState>:<>
      <p data-testid="za-shortlist-count">{rows.length} of 3 properties</p>
      {rows.map(row=><div key={row.investigation_id} className="za-history-item" data-testid="za-shortlist-member"><strong>Erf {row.request.subject_key.value.slice(-6)}</strong><ActionButton icon="remove" disabled={locked} aria-label={'Remove '+row.investigation_id} onClick={()=>void mutate('remove',row.investigation_id)}>Remove</ActionButton><NoteEditor row={row} locked={locked} onSave={note=>void mutate('note',row.investigation_id,note)}/></div>)}
      {rows.length<2?<EmptyState>Add at least two distinct properties to compare frozen evidence.</EmptyState>:
      <ScrollRegion label="Fictional property comparison" className="za-table-scroll"><table data-testid="za-comparison"><caption>Frozen fictional property comparison · no estimated value</caption>
        <thead><tr><th scope="col">Evidence</th>{rows.map(r=><th scope="col" key={r.investigation_id}>Erf {r.request.subject_key.value.slice(-6)}</th>)}</tr></thead>
        <tbody>
          <tr><th scope="row">User-reported asking price</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.subject.asking_price?formatZar(r.evidence.subject.asking_price):'Not provided'}</td>)}</tr>
          <tr><th scope="row">Analysis date / mode</th>{rows.map(r=><td key={r.investigation_id}>{r.request.analysis_date} · {r.request.mode==='as_of'?'Fictional as-of':'Retrospective'}</td>)}</tr>
          <tr><th scope="row">Dwelling / land (m²)</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.subject.dwelling_extent??'Unknown'} / {r.evidence.subject.land_extent??'Unknown'}</td>)}</tr>
          <tr><th scope="row">Comparable evidence</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.status==='fictional_supported'?r.evidence.selected_count+' fictional sales · '+r.evidence.window_days+' days':'Insufficient or unsupported evidence'}</td>)}</tr>
          <tr><th scope="row">Invented registered-sale consideration</th>{rows.map(r=><td key={r.investigation_id}>{r.evidence.comparables.length?r.evidence.comparables.map(s=><div key={s.event_id}>{s.reported_sale_date} · {formatZar(s.sale_consideration)}</div>):'No comparable sale amounts'}</td>)}</tr>
          <tr><th scope="row">Evidence qualification</th>{rows.map(r=><td className="za-explanation-cell" key={r.investigation_id}>{evidenceExplanation(r.evidence).reason} {evidenceModeLimit(r.evidence)}</td>)}</tr>
          <tr><th scope="row">Source build / matching policy</th>{rows.map(r=><td className="za-explanation-cell" key={r.investigation_id}>{r.evidence.data_build}<br/>{r.evidence.policy_version}</td>)}</tr>
          <tr><th scope="row">Suggested next step</th>{rows.map(r=><td className="za-explanation-cell" key={r.investigation_id}>{evidenceExplanation(r.evidence).next}</td>)}</tr>
          <tr><th scope="row">Saved decision notes</th>{rows.map(r=><td className="za-note-cell" key={r.investigation_id}>{r.note_text||'No note'}</td>)}</tr>
        </tbody></table></ScrollRegion>}
    </>}
  </section>;
}

function NoteEditor({row,locked,onSave}:{row:ShortlistMember;locked:boolean;onSave:(note:string)=>void}){
  const [draft,setDraft]=useState(row.note_text);
  useEffect(()=>{setDraft(row.note_text);},[row.note_text]);
  const id='za-note-'+row.investigation_id,valid=validDecisionNote(draft),dirty=draft!==row.note_text;
  return <div className="za-note-editor">
    <label htmlFor={id}>Decision note for Erf {row.request.subject_key.value.slice(-6)}</label>
    <textarea id={id} className="hpi-field" rows={3} value={draft} disabled={locked} aria-invalid={!valid} aria-describedby={id+'-hint'} onChange={e=>setDraft(e.target.value)}/>
    <p id={id+'-hint'} className="za-muted">{Array.from(draft).length}/800 characters · {valid?(dirty?'Unsaved draft':'Saved note (or empty)'):'Use at most 800 characters; no control characters except tabs and newlines.'}</p>
    <ActionButton icon="save" disabled={locked||!dirty||!valid} onClick={()=>onSave(draft)} aria-label={'Save note '+row.investigation_id}>Save note</ActionButton>{' '}
    <ActionButton icon="refresh" disabled={locked||!dirty} onClick={()=>setDraft(row.note_text)}>Discard draft</ActionButton>
  </div>;
}
