/** Dedicated fictional ZA response boundary. Never decode US or real evidence as ZA. */
export const VERSION='hpi-investigation-v2-fictional';
export const PATH='/v2/fictional/za/investigate';
export const NAMESPACE='za-fictional-erf';
export type Mode='as_of'|'retrospective';
export type Request={contract_version:typeof VERSION;market:'ZA';currency:'ZAR';area_unit:'m2';subject_key:{namespace:typeof NAMESPACE;value:string};analysis_date:string;mode:Mode;asking_price:string|null};
type Money={currency:'ZAR';minor_units:number;decimal:string};
type Comparable={property_key:{namespace:typeof NAMESPACE;value:string};event_id:string;reported_sale_date:string;registration_date:string;availability_date:string|null;sale_consideration:Money;dwelling_extent:string;land_extent:string;attribute_observed_date:string;attribute_effective_from:string;attribute_available_date:string|null;age_days:number;distance_squared_metres:number};
export type Result={status:'fictional_supported'|'insufficient_data'|'out_of_coverage';reason:string;mode:Mode;analysis_date:string;subject:{property_key:{namespace:typeof NAMESPACE;value:string};asking_price:Money|null;dwelling_extent?:string;land_extent?:string};selected_count:number;window_days:365|730|null;eligible_unique_by_window:{'365':number;'730':number};comparables:Comparable[];warnings:string[];fictional_as_of_qualified:boolean};
function fail():never{throw Error('Invalid fictional ZA response');}
function record(x:unknown):Record<string,unknown>{if(!x||typeof x!=='object'||Array.isArray(x))return fail();return x as Record<string,unknown>;}
function day(x:unknown):x is string{
  return typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x+'T00:00:00Z'))&&new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
}
function integer(x:unknown,min:number,max:number):x is number{return typeof x==='number'&&Number.isSafeInteger(x)&&x>=min&&x<=max;}
function parcel(x:unknown):string{const k=record(x);if(Object.keys(k).length!==2||k.namespace!==NAMESPACE||typeof k.value!=='string'||!/^fictional-erf-[0-9]{6}$/.test(k.value))return fail();return k.value;}
function extent(x:unknown):x is string{return typeof x==='string'&&/^[0-9]{1,7}(?:\.[0-9]{1,6})?$/.test(x)&&Number(x)>0&&Number(x)<=1_000_000;}
function cash(x:unknown):Money{
  const m=record(x);
  if(Object.keys(m).length!==3||m.currency!=='ZAR'||!integer(m.minor_units,1,100_000_000_000))return fail();
  const expected=String(Math.floor(m.minor_units/100))+'.'+String(m.minor_units%100).padStart(2,'0');
  if(m.decimal!==expected)return fail();
  return m as Money;
}
export function formatZar(m:Money):string{
  const [whole,cents]=m.decimal.split('.');
  return 'R '+whole!.replace(/\B(?=(\d{3})+(?!\d))/g,' ')+'.'+cents;
}
export function decode(x:unknown,request:Request):Result{
  const r=record(x),s=record(r.subject),counts=record(r.eligible_unique_by_window);
  if(r.contract_version!==VERSION||r.market!=='ZA'||r.currency!=='ZAR'||r.area_unit!=='m2'
    ||r.source_kind!=='synthetic_fixture'||r.data_build!=='za-fictional-build-v1'||r.policy_version!=='za-fictional-pinelands-v1'
    ||r.real_data_approved!==false||r.historical_as_of_verified!==false||r.valuation!==null
    ||r.analysis_date!==request.analysis_date||!day(r.analysis_date)||r.mode!==request.mode
    ||parcel(s.property_key)!==request.subject_key.value||s.asking_price_source!=='user_reported'
    ||r.radius_metres!==2000||r.minimum_comparables!==3||r.preferred_comparables!==5||r.extent_tolerance_percent!==25
    ||!integer(counts['365'],0,100)||!integer(counts['730'],0,100)||counts['365']>counts['730']
    ||typeof r.reason!=='string'||!Array.isArray(r.warnings)||r.warnings.length<2||!r.warnings.every(v=>typeof v==='string')
    ||!Array.isArray(r.comparables)||r.comparables.length!==r.selected_count||typeof r.fictional_as_of_qualified!=='boolean')return fail();
  if(request.asking_price===null){if(s.asking_price!==null)return fail();}
  else {const m=cash(s.asking_price);const [a,b='']=request.asking_price.split('.');if(m.minor_units!==Number(a)*100+Number(b.padEnd(2,'0')))return fail();}
  const supported=r.status==='fictional_supported';
  if(supported){
    if(!extent(s.dwelling_extent)||!extent(s.land_extent)||s.property_class!=='fictional-freehold-single-dwelling'
      ||s.locality!=='fictional-pinelands-study'||s.identity_scope!=='fictional_parcel_only'||s.building_identity_verified!==false
      ||(r.window_days!==365&&r.window_days!==730)||r.reason!==(r.window_days===365?'primary_window':'extended_window')
      ||(r.window_days===365?counts['365']<3:counts['365']>=3||counts['730']<3)
      ||r.selected_count!==Math.min(5,counts[String(r.window_days)] as number)
      ||r.fictional_as_of_qualified!==(request.mode==='as_of'))return fail();
  }else if(!['insufficient_data','out_of_coverage'].includes(String(r.status))||r.window_days!==null||r.selected_count!==0||r.fictional_as_of_qualified!==false||counts['730']>=3)return fail();
  if(s.dwelling_extent!==undefined&&!extent(s.dwelling_extent)||s.land_extent!==undefined&&!extent(s.land_extent))return fail();
  const seen=new Set<string>(),events=new Set<string>();
  for(const item of r.comparables){
    const v=record(item),k=parcel(v.property_key);
    if(k===request.subject_key.value||seen.has(k)||typeof v.event_id!=='string'||!/^fictional-event-[0-9]{6}-[a-z]+$/.test(v.event_id)||events.has(v.event_id)
      ||v.source_type!=='invented_registered_sale'||!day(v.reported_sale_date)||!day(v.registration_date)||v.registration_date<v.reported_sale_date
      ||v.reported_sale_date>=request.analysis_date||!integer(v.age_days,1,Number(r.window_days))
      ||v.age_days!==(Date.parse(request.analysis_date)-Date.parse(v.reported_sale_date))/86400000
      ||!integer(v.distance_squared_metres,1,4_000_000)||!extent(v.dwelling_extent)||!extent(v.land_extent)
      ||!day(v.attribute_observed_date)||!day(v.attribute_effective_from)||v.attribute_effective_from>v.reported_sale_date
      ||(v.availability_date!==null&&(!day(v.availability_date)||v.availability_date<v.registration_date))
      ||(v.attribute_available_date!==null&&(!day(v.attribute_available_date)||v.attribute_available_date<v.attribute_observed_date)))return fail();
    if(request.mode==='as_of'&&(!day(v.availability_date)||v.availability_date>request.analysis_date||!day(v.attribute_available_date)||v.attribute_available_date>request.analysis_date))return fail();
    const a=Number(s.dwelling_extent),b=Number(s.land_extent),d=Number(v.dwelling_extent),l=Number(v.land_extent);
    if(d<a*.75||d>a*1.25||l<b*.75||l>b*1.25)return fail();
    cash(v.sale_consideration);seen.add(k);events.add(v.event_id);
  }
  return r as unknown as Result;
}

export const SAVED_PATH='/v2/fictional/za/saved';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
export type Saved={investigation_id:string;request:Request;evidence:Result};
export function decodeSaved(x:unknown):Saved{
  const r=record(x),q=record(r.request);
  if(Object.keys(r).sort().join(' ')!=='evidence investigation_id request'||typeof r.investigation_id!=='string'||!UUID.test(r.investigation_id)
    ||Object.keys(q).sort().join(' ')!=='analysis_date area_unit asking_price contract_version currency market mode subject_key'
    ||q.contract_version!==VERSION||q.market!=='ZA'||q.currency!=='ZAR'||q.area_unit!=='m2'
    ||!day(q.analysis_date)||!['as_of','retrospective'].includes(String(q.mode))
    
    ||(q.asking_price!==null&&(typeof q.asking_price!=='string'||!/^[0-9]{1,10}(?:\.[0-9]{1,2})?$/.test(q.asking_price))))return fail();
  parcel(q.subject_key);
  const request=q as unknown as Request;
  return {investigation_id:r.investigation_id,request,evidence:decode(r.evidence,request)};
}
export function decodeHistory(x:unknown):{investigations:Saved[];truncated:boolean}{
  const r=record(x);
  if(r.market!=='ZA'||r.source_kind!=='synthetic_fixture'||typeof r.truncated!=='boolean'||!Array.isArray(r.investigations)||r.investigations.length>30)return fail();
  const investigations=r.investigations.map(decodeSaved);
  if(new Set(investigations.map(x=>x.investigation_id)).size!==investigations.length)return fail();
  return {investigations,truncated:r.truncated};
}

export const SHORTLIST_PATH='/v2/fictional/za/shortlist';
export function decodeShortlist(x:unknown):Saved[]{
  const r=record(x);
  if(Object.keys(r).sort().join(' ')!=='comparison_ready investigations market source_kind'||r.market!=='ZA'||r.source_kind!=='synthetic_fixture'
    ||!Array.isArray(r.investigations)||r.investigations.length>3||r.comparison_ready!==(r.investigations.length>=2))return fail();
  const rows=r.investigations.map(decodeSaved);
  if(new Set(rows.map(row=>row.investigation_id)).size!==rows.length||new Set(rows.map(row=>row.request.subject_key.value)).size!==rows.length)return fail();
  return rows;
}
