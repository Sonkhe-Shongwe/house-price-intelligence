import {useState,useRef,useEffect,type FormEvent} from 'react';
import {ActionButton,Field,PageHeading,StatusMessage,LoadingState,EmptyState,ScrollRegion} from './UI';
import {PATH,VERSION,canonicalPrice,formatUSD,decode,type Request,type Result} from './nycInvestigationContract';
import './nycInvestigation.css';

const messages={
  supported:'Sufficient comparable evidence',
  insufficient_data:'Insufficient comparable evidence',
  ambiguous_address:'Address cannot be resolved uniquely',
  out_of_coverage:'Outside supported fixture coverage',
  evidence_unavailable:'Evidence unavailable',
};
const examples=['Fictional NYC Home A','Fictional NYC Home B','Fictional NYC Home C','Fictional NYC Ambiguous','Fictional NYC Unsupported','Fictional NYC Unknown'];
export default function NYCInvestigation(){
  const [address,setAddress]=useState(examples[0]!);
  const [price,setPrice]=useState('650000.01');
  const [result,setResult]=useState<Result|null>(null),[error,setError]=useState(''),[pending,setPending]=useState(false);
  const flight=useRef<AbortController|null>(null);
  useEffect(()=>()=>flight.current?.abort(),[]);
  function clear(){setResult(null);setError('');}
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();if(flight.current)return;clear();
    let amount:string|null;
    try{amount=canonicalPrice(price||null);}catch{setError('Enter a positive fictional USD amount with up to two decimal places.');return;}
    const request:Request={contract_version:VERSION,address,asking_price_usd:amount};
    const controller=new AbortController();flight.current=controller;setPending(true);
    try{
      const res=await fetch(PATH,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal});
      if(!res.ok||res.headers.get('X-Synthetic-Only')!=='true')throw Error('Unavailable');
      const value=decode(await res.json(),request);
      if(!controller.signal.aborted&&flight.current===controller)setResult(value);
    }catch{if(!controller.signal.aborted)setError('Investigation unavailable. No evidence shown or saved. Retry the fictional request.');}
    finally{if(flight.current===controller){flight.current=null;if(!controller.signal.aborted)setPending(false);}}
  }
  return <main className="nyc-study source-shell" data-testid="nyc-study">
    <nav aria-label="Fictional workspace"><a href="/buyer-workflow">Existing fictional workspace</a><span aria-current="page">NYC investigation</span></nav>
    <PageHeading eyebrow="HPI / NYC / FICTIONAL REHEARSAL" title="Investigate a property" description="Queens · ZIP 11361 · A2. Invented demonstration records only. No live address lookup, market valuation or saved investigation."/>
    <div className="nyc-layout">
      <section className="nyc-panel" aria-labelledby="nyc-input-heading">
        <h2 id="nyc-input-heading">Investigation inputs</h2>
        <form onSubmit={submit} noValidate><fieldset disabled={pending}>
          <label htmlFor="nyc-address">Fictional address</label>
          <select id="nyc-address" value={address} onChange={e=>{setAddress(e.target.value);clear();}}>
            {examples.map(v=><option key={v}>{v}</option>)}
          </select>
          <Field id="nyc-price" label="Fictional asking price (USD)" hint="Optional. Buyer-reported amount, separate from completed sales." inputMode="decimal" value={price} maxLength={15} onChange={e=>{setPrice(e.target.value);clear();}}/>
          <ActionButton icon="search" variant="primary" type="submit" data-testid="nyc-submit" disabled={pending}>{pending?'Investigating…':'Investigate'}</ActionButton>
        </fieldset></form>
        <p className="nyc-muted">Fixed fictional addresses, not autocomplete. No information is saved.</p>
      </section>
      <section className="nyc-panel" aria-labelledby="nyc-evidence-heading" aria-busy={pending}>
        <h2 id="nyc-evidence-heading">Comparable sales evidence</h2>
        {pending?<LoadingState>Checking fictional evidence…</LoadingState>:error?<StatusMessage tone="error">{error}</StatusMessage>:!result?<EmptyState>Select a fictional home and investigate to see the evidence.</EmptyState>:
          <div data-testid="nyc-result">
            <StatusMessage tone={result.status==='supported'?'success':'info'}>{messages[result.status]}</StatusMessage>
            {result.subject&&<h3>{result.subject.address}</h3>}
            <dl className="nyc-metrics">
              <div><dt>Buyer-reported asking price</dt><dd>{formatUSD(result.asking_price_usd)}</dd></div>
              <div><dt>Snapshot gross area</dt><dd>{result.subject?result.subject.snapshot_gross_area_sqft.toLocaleString('en-US')+' ft²':'Unavailable'}</dd></div>
            </dl>
            {result.comparables.length>0?<ScrollRegion label="Fictional completed sales" className="nyc-table-scroll">
              <table><caption>Earlier completed sales (invented)</caption><thead><tr><th scope="col">Comparable</th><th scope="col">Sale date</th><th scope="col">Sale price</th><th scope="col">Gross area</th><th scope="col">Area difference</th></tr></thead>
                <tbody>{result.comparables.map(s=><tr key={s.rank} data-testid="nyc-comparable"><th scope="row">{s.rank}</th><td>{s.sale_date}</td><td>{formatUSD(s.sale_price_usd)}</td><td>{s.snapshot_gross_area_sqft.toLocaleString('en-US')} ft²</td><td>{s.absolute_area_difference_sqft.toLocaleString('en-US')} ft²</td></tr>)}</tbody></table>
            </ScrollRegion>:<EmptyState>No comparable sale amounts shown. {result.status==='ambiguous_address'?'Confirm unique property identity before comparison.':'Do not infer a selling price from unavailable evidence.'}</EmptyState>}
            <section className="nyc-method" aria-label="Method and limitations">
              <h3>Method and limitations</h3>
              <p>Same-release gross area, AreaSource 2. Earlier verified-deed screening simulated with invented records; price-free ranking within 25% area, 3–5 distinct other properties required.</p>
              <dl className="nyc-provenance"><dt>Analysis date</dt><dd>{result.analysis_date}</dd><dt>Snapshot publication</dt><dd>{result.snapshot_publication_date}</dd><dt>Invented version</dt><dd>{result.snapshot_version}</dd><dt>Sales coverage</dt><dd>{result.sales_covered_from} to {result.sales_covered_through}</dd></dl>
              <p>{result.lookback_fully_covered?'Full fictional lookback window.':'Incomplete 365-day lookback window.'} Current-snapshot comparison, not sale-time area or historical as-of evidence. No price per square foot or valuation.</p>
            </section>
          </div>}
      </section>
    </div>
  </main>;
}
