import {useState,useRef,useEffect,type FormEvent} from 'react';
import {ActionButton,Field,PageHeading,StatusMessage,LoadingState,EmptyState,ScrollRegion} from './UI';
import {decode,decodeSaved,decodeHistory,formatZar,VERSION,PATH,SAVED_PATH,NAMESPACE,type Request,type Result,type Mode,type Saved} from './saInvestigationContract';
import './saInvestigation.css';

const reasons:Record<string,string>={subject_identity_unresolved:'The selected fictional parcel cannot be resolved exactly.',
  subject_attributes_or_location_unqualified:'Dated extent or location evidence is insufficient.',
  unsupported_fixture_class_or_locality:'The property is outside this fictional study scope.',
  fewer_than_three_qualified_fixture_parcels:'Fewer than three distinct earlier properties qualify.'};
export default function SouthAfricanInvestigation(){
  const [subject,setSubject]=useState('fictional-erf-000001'),[day,setDay]=useState('2025-07-01'),[mode,setMode]=useState<Mode>('as_of'),[price,setPrice]=useState('2500000.01');
  const [result,setResult]=useState<Result|null>(null),[pending,setPending]=useState(false),[error,setError]=useState('');
  const flight=useRef<AbortController|null>(null),retry=useRef<string|null>(null),requestRef=useRef<Request|null>(null);
  const [saved,setSaved]=useState<Saved[]>([]),[savingEnabled,setSavingEnabled]=useState(false),[savedId,setSavedId]=useState<string|null>(null),[savedNotice,setSavedNotice]=useState(''),[truncated,setTruncated]=useState(false);
  async function refresh(signal:AbortSignal){
    const res=await fetch(SAVED_PATH,{cache:'no-store',credentials:'same-origin',redirect:'error',signal});
    if(res.status===404){setSavingEnabled(false);return;}
    if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('history unavailable');
    const history=decodeHistory(await res.json());setSaved(history.investigations);setTruncated(history.truncated);setSavingEnabled(true);
  }
  useEffect(()=>{
    const controller=new AbortController();
    refresh(controller.signal).catch(()=>{if(!controller.signal.aborted)setSavedNotice('Saved history unavailable.');});
    return()=>{controller.abort();flight.current?.abort();};
  },[]);
  function clear(){setResult(null);setError('');setSavedId(null);setSavedNotice('');retry.current=null;requestRef.current=null;}
  async function save(){
    if(flight.current||!requestRef.current||!result||savedId)return;
    const request=requestRef.current;const id=retry.current??crypto.randomUUID();retry.current=id;
    const controller=new AbortController();flight.current=controller;setPending(true);setSavedNotice('');
    try{
      const res=await fetch(SAVED_PATH,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({retry_id:id,request}),credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal});
      if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('save unavailable');
      const row=decodeSaved(await res.json());
      if(row.investigation_id!==id||JSON.stringify(row.request.subject_key)!==JSON.stringify(request.subject_key)||row.request.analysis_date!==request.analysis_date||row.request.mode!==request.mode||row.request.asking_price!==request.asking_price)throw Error('save mismatch');
      setResult(row.evidence);setSavedId(id);setSaved(old=>[row,...old.filter(x=>x.investigation_id!==id)].slice(0,30));setSavedNotice('Saved in this local server session.');
      try{await refresh(controller.signal);}catch{if(!controller.signal.aborted)setSavedNotice('Saved. History refresh unavailable.');}
    }catch{if(!controller.signal.aborted)setSavedNotice('Save not confirmed. Retry uses the same identifier; no duplicate save is requested.');}
    finally{if(flight.current===controller){flight.current=null;if(!controller.signal.aborted)setPending(false);}}
  }
  async function reopen(id:string){
    if(flight.current)return;
    clear();const controller=new AbortController();flight.current=controller;setPending(true);
    try{
      const res=await fetch(SAVED_PATH+'/'+id,{credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal});
      if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('reopen unavailable');
      const row=decodeSaved(await res.json());if(row.investigation_id!==id)throw Error('reopen mismatch');
      setSubject(row.request.subject_key.value);setDay(row.request.analysis_date);setMode(row.request.mode);setPrice(row.request.asking_price??'');
      setResult(row.evidence);setSavedId(id);requestRef.current=row.request;setSavedNotice('Reopened frozen evidence; not recalculated.');
    }catch{if(!controller.signal.aborted){setError('Saved investigation unavailable. No evidence shown.');}}
    finally{if(flight.current===controller){flight.current=null;if(!controller.signal.aborted)setPending(false);}}
  }
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();if(flight.current)return;
    clear();
    if(price&&!/^[0-9]{1,10}(?:\.[0-9]{1,2})?$/.test(price)){setError('Enter a positive fictional ZAR amount with up to two decimal places.');return;}
    const request:Request={contract_version:VERSION,market:'ZA',currency:'ZAR',area_unit:'m2',subject_key:{namespace:NAMESPACE,value:subject},analysis_date:day,mode,asking_price:price||null};
    const controller=new AbortController();flight.current=controller;setPending(true);
    try{
      const res=await fetch(PATH,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal});
      if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('unavailable');
      setResult(decode(await res.json(),request));requestRef.current=request;
    }catch{if(!controller.signal.aborted)setError('Investigation unavailable. Check the fictional inputs or retry. No result was saved.');}
    finally{if(flight.current===controller){flight.current=null;if(!controller.signal.aborted)setPending(false);}}
  }
  return <main className="za-study" data-testid="za-study">
    <nav aria-label="Market previews"><a href="/buyer-workflow">US fictional buyer workspace</a><span aria-current="page">South Africa</span></nav>
    <PageHeading eyebrow="HPI / ZA / FICTIONAL REHEARSAL" title="Investigate a South African property" description="Explore historical comparable-sale evidence in a fictional Pinelands-inspired study. No real addresses, live prices or valuations."/>
    <div className="za-layout">
      <section className="za-panel" aria-labelledby="za-input-heading">
        <h2 id="za-input-heading">Investigation inputs</h2>
        <form onSubmit={submit}><fieldset disabled={pending}>
          <label htmlFor="za-parcel">Fictional erf</label>
          <select className="hpi-field" id="za-parcel" value={subject} onChange={e=>{setSubject(e.target.value);clear();}}>
            <option value="fictional-erf-000001">Erf 000001 · study subject</option>
            <option value="fictional-erf-000010">Erf 000010 · ambiguous identity</option>
            <option value="fictional-erf-000015">Erf 000015 · unsupported class</option>
            {!["fictional-erf-000001","fictional-erf-000010","fictional-erf-000015"].includes(subject)&&<option value={subject}>Erf {subject.slice(-6)} · saved fictional enquiry</option>}
          </select>
          <Field id="za-date" type="date" label="Analysis date" value={day} required onChange={e=>{setDay(e.target.value);clear();}}/>
          <label htmlFor="za-mode">Evidence mode</label>
          <select className="hpi-field" id="za-mode" value={mode} onChange={e=>{setMode(e.target.value as Mode);clear();}}>
            <option value="as_of">Fictional as-of evidence</option><option value="retrospective">Retrospective research</option>
          </select>
          <Field id="za-price" inputMode="decimal" label="Fictional asking price (ZAR)" value={price} maxLength={13} hint="Optional. Separate from sale consideration; not a ranking input." onChange={e=>{setPrice(e.target.value);clear();}}/>
          <ActionButton icon="search" variant="primary" type="submit" data-testid="za-submit">Investigate</ActionButton>
        </fieldset></form>
        <p className="za-muted">{savingEnabled?'Investigate first, then save explicitly. Saved evidence lasts only for this local server session.':'Stateless preview. No investigation or shortlist is saved.'}</p>
        {savingEnabled&&<ActionButton icon="save" disabled={!result||pending||savedId!==null} onClick={save} data-testid="za-save">Save investigation</ActionButton>}
        {savedNotice&&<StatusMessage>{savedNotice}</StatusMessage>}
        {savedId&&<p className="za-muted" data-testid="za-saved-id">Saved ID: {savedId}</p>}
      </section>
      <section className="za-panel" aria-labelledby="za-evidence-heading" aria-busy={pending}>
        <h2 id="za-evidence-heading">Comparable evidence</h2>
        {pending?<LoadingState>Checking fictional sale and extent evidence…</LoadingState>:error?<StatusMessage tone="error">{error}</StatusMessage>:!result?<EmptyState>Choose a fictional property and investigate to see evidence.</EmptyState>:
        <div data-testid="za-result">
          {result.status==='fictional_supported'?<>
            <StatusMessage tone="success">{result.selected_count} fictional comparable properties</StatusMessage>
            <dl className="za-metrics"><div><dt>Asking price</dt><dd>{result.subject.asking_price?formatZar(result.subject.asking_price):'Not provided'}</dd></div><div><dt>Dwelling / land</dt><dd>{result.subject.dwelling_extent} / {result.subject.land_extent} m²</dd></div><div><dt>Selected window</dt><dd>{result.window_days} days</dd></div><div><dt>Eligible, 365 / 730 days</dt><dd>{result.eligible_unique_by_window['365']} / {result.eligible_unique_by_window['730']}</dd></div></dl>
            <p>{result.fictional_as_of_qualified?'Fictional as-of qualification only.':'Retrospective only; historical availability is not established.'}</p>
            <ScrollRegion label="Fictional comparable sales" className="za-table-scroll"><table><caption>Invented registered-sale consideration, not estimated value</caption><thead><tr><th scope="col">Erf</th><th scope="col">Sale date</th><th scope="col">Consideration (ZAR)</th><th scope="col">Dwelling / land (m²)</th><th scope="col">Grid distance (m)</th><th scope="col">Available</th></tr></thead><tbody>{result.comparables.map(s=><tr key={s.event_id} data-testid="za-comparable"><td>{s.property_key.value.slice(-6)}</td><td>{s.reported_sale_date}</td><td>{formatZar(s.sale_consideration)}</td><td>{s.dwelling_extent} / {s.land_extent}</td><td>{Math.sqrt(s.distance_squared_metres).toFixed(1)}</td><td>{s.availability_date??'Unknown'}</td></tr>)}</tbody></table></ScrollRegion>
          </>:<StatusMessage>{reasons[result.reason]??'Insufficient fictional evidence.'} No comparable sale amounts are shown.</StatusMessage>}
          <p className="za-muted">No real property identity, geographic distance or historical availability verified. No valuation.</p>
        </div>}
      </section>
    </div>
    {savingEnabled&&<section className="za-panel za-method" aria-labelledby="za-history-heading"><h2 id="za-history-heading">Saved South African investigations</h2>
      <p className="za-muted">Fictional workspace only. Not saved after server restart. {truncated?'History limited to 30 records.':''}</p>
      {saved.length===0?<EmptyState>No saved investigations.</EmptyState>:<div className="za-history">{saved.map(row=><div key={row.investigation_id} className="za-history-item"><div><strong>Erf {row.request.subject_key.value.slice(-6)}</strong><p>{row.request.analysis_date} · {row.evidence.selected_count} fictional comparables</p><p>{row.evidence.subject.asking_price?formatZar(row.evidence.subject.asking_price):'No asking price'}</p></div><ActionButton icon="open" disabled={pending} onClick={()=>reopen(row.investigation_id)} data-testid="za-reopen" aria-label={'Reopen '+row.investigation_id}>Reopen</ActionButton></div>)}</div>}
    </section>}
    <section className="za-panel za-method"><h2>How evidence is selected</h2><p>Exact fictional parcel identity; both dwelling and land extents within 25%; invented grid radius of 2 km; earlier 365-day window, extended to 730 days if fewer than three qualify. Up to five distinct properties, ranked without prices. No real map is displayed.</p></section>
  </main>;
}
