import {useState,useRef,useEffect,type FormEvent} from 'react';
import {ActionButton,Field,PageHeading,StatusMessage,LoadingState,EmptyState,ScrollRegion} from './UI';
import {decode,formatZar,VERSION,PATH,NAMESPACE,type Request,type Result,type Mode} from './saInvestigationContract';
import './saInvestigation.css';

const reasons:Record<string,string>={subject_identity_unresolved:'The selected fictional parcel cannot be resolved exactly.',
  subject_attributes_or_location_unqualified:'Dated extent or location evidence is insufficient.',
  unsupported_fixture_class_or_locality:'The property is outside this fictional study scope.',
  fewer_than_three_qualified_fixture_parcels:'Fewer than three distinct earlier properties qualify.'};
export default function SouthAfricanInvestigation(){
  const [subject,setSubject]=useState('fictional-erf-000001'),[day,setDay]=useState('2025-07-01'),[mode,setMode]=useState<Mode>('as_of'),[price,setPrice]=useState('2500000.01');
  const [result,setResult]=useState<Result|null>(null),[pending,setPending]=useState(false),[error,setError]=useState('');
  const flight=useRef<AbortController|null>(null);
  useEffect(()=>()=>flight.current?.abort(),[]);
  function clear(){setResult(null);setError('');}
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();if(flight.current)return;
    clear();
    if(price&&!/^[0-9]{1,10}(?:\.[0-9]{1,2})?$/.test(price)){setError('Enter a positive fictional ZAR amount with up to two decimal places.');return;}
    const request:Request={contract_version:VERSION,market:'ZA',currency:'ZAR',area_unit:'m2',subject_key:{namespace:NAMESPACE,value:subject},analysis_date:day,mode,asking_price:price||null};
    const controller=new AbortController();flight.current=controller;setPending(true);
    try{
      const res=await fetch(PATH,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal});
      if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('unavailable');
      setResult(decode(await res.json(),request));
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
          </select>
          <Field id="za-date" type="date" label="Analysis date" value={day} required onChange={e=>{setDay(e.target.value);clear();}}/>
          <label htmlFor="za-mode">Evidence mode</label>
          <select className="hpi-field" id="za-mode" value={mode} onChange={e=>{setMode(e.target.value as Mode);clear();}}>
            <option value="as_of">Fictional as-of evidence</option><option value="retrospective">Retrospective research</option>
          </select>
          <Field id="za-price" inputMode="decimal" label="Fictional asking price (ZAR)" value={price} maxLength={13} hint="Optional. Separate from sale consideration; not a ranking input." onChange={e=>{setPrice(e.target.value);clear();}}/>
          <ActionButton icon="search" variant="primary" type="submit" data-testid="za-submit">Investigate</ActionButton>
        </fieldset></form>
        <p className="za-muted">Stateless preview. No investigation or shortlist is saved.</p>
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
    <section className="za-panel za-method"><h2>How evidence is selected</h2><p>Exact fictional parcel identity; both dwelling and land extents within 25%; invented grid radius of 2 km; earlier 365-day window, extended to 730 days if fewer than three qualify. Up to five distinct properties, ranked without prices. No real map is displayed.</p></section>
  </main>;
}
