import {useEffect,useState} from 'react';
import {formatExactUsd,type InvestigationView} from './evidenceBridge';
import {fixtureFetch} from './fixtureFetch';

type Sale={rank:number;sale_date:string;sale_price_usd:string;age_days:number;area_difference_pct:number;assessment_year:number;location_evidence:string};
function exactObject(value:unknown,keys:string):Record<string,unknown>{
  if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Invalid preview');
  const v=value as Record<string,unknown>;
  if(Object.keys(v).sort().join(' ')!==keys.split(' ').sort().join(' '))throw Error('Invalid preview fields');
  return v;
}
function adapt(raw:unknown,record:InvestigationView):Sale[]{
  const r=exactObject(raw,'contract_version investigation_id source_kind status tier analysis_date selected_count sales asking_price_usd asking_price_source provenance geometry_available building_identity_verified valuation');
  const p=exactObject(r.provenance,'build_id built_at_utc publisher_attributed historical_asof_verified public_display_approved');
  if(r.contract_version!=='buyer-evidence-preview-v1'||r.investigation_id!==record.investigationId
    ||r.source_kind!=='synthetic_fixture'||r.status!==record.status||r.tier!==record.tier
    ||r.analysis_date!==record.analysisDate||r.selected_count!==record.selectedCount
    ||r.asking_price_source!=='buyer_reported'||r.geometry_available!==false||r.building_identity_verified!==false||r.valuation!==null
    ||p.build_id!==record.sourceBuildId||p.built_at_utc!==record.sourceBuiltAtUtc
    ||p.publisher_attributed!==false||p.historical_asof_verified!==false||p.public_display_approved!==false
    ||(r.asking_price_usd===null?'Not supplied':typeof r.asking_price_usd==='string'?formatExactUsd(r.asking_price_usd):'invalid')!==record.askingPriceText
    ||!Array.isArray(r.sales)||r.sales.length!==record.selectedCount)throw Error('Preview does not match frozen evidence');
  return r.sales.map((item:unknown,i:number)=>{
    const s=exactObject(item,'rank sale_date sale_price_usd age_days area_difference_pct assessment_year location_evidence');
    const original=record.comparables[i]!;
    if(s.rank!==i+1||s.sale_date!==original.saleDate||s.sale_price_usd!==original.exactPriceUsd
      ||s.age_days!==original.ageDays||s.area_difference_pct!==original.areaDifferencePct
      ||s.assessment_year!==Number(original.saleDate.slice(0,4))-1
      ||s.location_evidence!==(original.sameNeighbourhood?'same_neighbourhood':'exploratory_spatial'))throw Error('Preview sale mismatch');
    return s as Sale;
  });
}
export default function BuyerEvidencePreview({record}:{record:InvestigationView}){
  const [requested,setRequested]=useState(false);
  const [sales,setSales]=useState<Sale[]|null>(null);
  const [error,setError]=useState(false);
  useEffect(()=>{
    if(!requested)return;
    const ctrl=new AbortController();
    setSales(null);setError(false);
    void (async()=>{
      try{
        const res=await fixtureFetch('/v1/investigations/'+record.investigationId+'/evidence-preview',{signal:ctrl.signal});
        if(!res.ok)throw Error('Unavailable');
        const result=adapt(await res.json(),record);
        if(!ctrl.signal.aborted)setSales(result);
      }catch{if(!ctrl.signal.aborted)setError(true);}
    })();
    return ()=>ctrl.abort();
  },[requested,record]);
  return <section className="hpi-provenance" aria-label="Minimised buyer evidence preview">
    <h3>Buyer evidence preview</h3>
    <p>Fictional release rehearsal. Internal parcel and transaction identifiers, raw coordinates and free-text inputs are omitted. No publisher data is displayed.</p>
    <button type="button" data-testid="buyer-preview-load" disabled={requested&&!error} onClick={()=>{if(error){setRequested(false);setError(false);}else setRequested(true);}}>{error?'Reset preview':'View minimised evidence'}</button>
    {requested&&!sales&&!error&&<p role="status">Checking frozen evidence…</p>}
    {error&&<p role="alert" data-testid="buyer-preview-error">Evidence preview unavailable. The original saved investigation is unchanged.</p>}
    {sales&&<div data-testid="buyer-preview-result">
      <p>Analysis date: {record.analysisDate}. Fixture revision: {record.sourceBuiltAtUtc}. This is not a source publication date. No valuation or building position is established.</p>
      {sales.length===0?<p>No eligible comparable sales.</p>:<ol>{sales.map(s=><li key={s.rank} data-testid="buyer-preview-sale">
        <strong>{formatExactUsd(s.sale_price_usd)}</strong> · {s.sale_date} · {s.age_days} days earlier · {s.area_difference_pct}% area difference · Prior assessment {s.assessment_year} · {s.location_evidence==='same_neighbourhood'?'Same neighbourhood':'Exploratory spatial evidence'}
      </li>)}</ol>}
    </div>}
  </section>;
}
