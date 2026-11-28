/** Private historical-shape wire contract. No synthetic fallback or disclosure expansion. */
export type Sale={rank:number;sale_date:string;sale_price_usd:string;assessment_year:number;assessed_area_sqft:number;area_difference_pct:number;age_days:number;location_evidence:string};
export type Result={investigation_id:string;status:string;analysis_date:string;selected_count:number;sales:Sale[];asking_price_usd:string|null;buyer_reported_area_sqft:number;provenance:{build_revision:string;retrieved_at_utc:string}};
export const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
function record(x:unknown):Record<string,unknown>{
  if(!x||typeof x!=='object'||Array.isArray(x))throw Error('Unavailable');
  return x as Record<string,unknown>;
}
function exact(r:Record<string,unknown>,keys:string){
  if(Object.keys(r).sort().join(' ')!==keys.split(' ').sort().join(' '))throw Error('Unavailable');
}
function dateOnly(x:unknown):x is string{
  if(typeof x!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(x))return false;
  const t=Date.parse(x+'T00:00:00Z');
  return Number.isFinite(t)&&new Date(t).toISOString().slice(0,10)===x;
}
export function decode(x:unknown):Result{
  const r=record(x);
  exact(r,'investigation_id contract_version source_kind status tier analysis_date selected_count sales asking_price_usd asking_price_source buyer_reported_area_sqft provenance building_identity_verified geometry_available valuation');
  const p=record(r.provenance);
  exact(p,'publisher_attributed build_revision retrieved_at_utc historical_asof_verified public_display_approved');
  if(r.contract_version!=='historical-beta-evidence-v1'||r.source_kind!=='historical_shape_rehearsal'
    ||typeof r.investigation_id!=='string'||!UUID.test(r.investigation_id)
    ||r.valuation!==null||r.geometry_available!==false||r.building_identity_verified!==false
    ||p.publisher_attributed!==false||p.historical_asof_verified!==false||p.public_display_approved!==false
    ||r.asking_price_source!=='buyer_reported'||!dateOnly(r.analysis_date)
    ||typeof r.buyer_reported_area_sqft!=='number'||!Number.isFinite(r.buyer_reported_area_sqft)||r.buyer_reported_area_sqft<=0
    ||typeof p.build_revision!=='string'||!p.build_revision||typeof p.retrieved_at_utc!=='string'||!Number.isFinite(Date.parse(p.retrieved_at_utc))
    ||!['supported_neighbourhood','exploratory_spatial','insufficient_data','out_of_coverage'].includes(String(r.status))
    ||!Array.isArray(r.sales)||r.sales.length!==r.selected_count||r.sales.length>5
    ||!((r.status==='supported_neighbourhood'&&r.tier==='same_neighborhood'&&r.sales.length>=3)||(r.status==='exploratory_spatial'&&r.tier==='spatial_fallback'&&r.sales.length>=3)||((r.status==='insufficient_data'||r.status==='out_of_coverage')&&r.tier==='none'&&r.sales.length===0))
    ||(r.asking_price_usd!==null&&(typeof r.asking_price_usd!=='string'||!/^[0-9]+\.[0-9]{2}$/.test(r.asking_price_usd))))throw Error('Unavailable');
  for(const [i,item] of r.sales.entries()){
    const s=record(item);
    exact(s,'rank sale_date sale_price_usd assessment_year assessed_area_sqft area_difference_pct age_days location_evidence');
    if(s.rank!==i+1||typeof s.sale_price_usd!=='string'||!/^[0-9]+\.[0-9]{2}$/.test(s.sale_price_usd)
       ||!dateOnly(s.sale_date)||typeof s.assessed_area_sqft!=='number'||!Number.isFinite(s.assessed_area_sqft)||s.assessed_area_sqft<1000||s.assessed_area_sqft>1800
       ||s.assessment_year!==Number(s.sale_date.slice(0,4))-1
       ||typeof s.age_days!=='number'||!Number.isInteger(s.age_days)||s.age_days<1||s.age_days>365||s.age_days!==(Date.parse(r.analysis_date+'T00:00:00Z')-Date.parse(s.sale_date+'T00:00:00Z'))/86400000
       ||typeof s.area_difference_pct!=='number'||!Number.isFinite(s.area_difference_pct)||s.area_difference_pct<0||s.area_difference_pct>25
       ||(r.status==='supported_neighbourhood'&&s.location_evidence!=='same_neighbourhood')
       ||!['same_neighbourhood','exploratory_spatial'].includes(String(s.location_evidence)))throw Error('Unavailable');
  }
  return r as unknown as Result;
}
export type Entry={investigation_id:string;note_text:string;investigation:Result};
export type Comparison={shortlist_id:string;label:string;entries:Entry[]};
export function decodeComparison(x:unknown):Comparison{
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
export type SavedInvestigation={investigation_id:string;analysis_date:string;status:string;created_at_utc:string};
export type SavedShortlist={shortlist_id:string;label:string;created_at_utc:string};
export type Workspace={investigations:SavedInvestigation[];comparisons:SavedShortlist[];truncated:boolean};
export function decodeWorkspace(x:unknown):Workspace{
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
export type SearchResult={status:'one_eligible_candidate';addressId:string}|{status:'ambiguous'|'no_match'};
export function decodeSearch(x:unknown):SearchResult{
  const m=record(x);
  if(m.status==='one_eligible_candidate'&&typeof m.address_id==='string'&&/^[a-z0-9-]{1,40}$/.test(m.address_id))return {status:m.status,addressId:m.address_id};
  if(m.status==='ambiguous'||m.status==='no_match')return {status:m.status};
  throw Error('Unavailable');
}
export function decodeLogout(x:unknown):void{
  if(record(x).logged_out!==true)throw Error('Sign out unavailable');
}
