/** Strict response projection for the fixed NYC fictional service, not a real-data client. */
export const PATH='/v2/fictional/nyc/investigate';
export const VERSION='nyc-buyer-fixture-v1';
export type Request={contract_version:typeof VERSION;address:string;asking_price_usd:string|null};
type Status='supported'|'insufficient_data'|'ambiguous_address'|'out_of_coverage'|'evidence_unavailable';
type Subject={address:string;snapshot_gross_area_sqft:number};
type Comparable={rank:number;sale_date:string;sale_price_usd:string;age_days:number;snapshot_gross_area_sqft:number;absolute_area_difference_sqft:number};
export type Result={status:Status;subject:Subject|null;comparables:Comparable[];asking_price_usd:string|null;analysis_date:string;snapshot_publication_date:string;snapshot_version:string;sales_covered_from:string;sales_covered_through:string;lookback_fully_covered:boolean};
function ensure(value:unknown):asserts value {if(!value)throw Error('Invalid fictional NYC evidence');}
function obj(value:unknown,keys:string[]):Record<string,unknown>{
  ensure(value&&typeof value==='object'&&!Array.isArray(value));
  const r=value as Record<string,unknown>;
  ensure(Object.keys(r).length===keys.length&&keys.every(k=>Object.hasOwn(r,k)));
  return r;
}
function text(value:unknown):string {ensure(typeof value==='string');return value;}
function num(value:unknown,min:number):number{ensure(typeof value==='number'&&Number.isSafeInteger(value)&&value>=min);return value;}
function day(value:unknown):string{
  const s=text(value);
  ensure(/^\d{4}-\d{2}-\d{2}$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s);
  return s;
}
function age(a:string,b:string){return (Date.parse(a)-Date.parse(b))/86400000;}
export function canonicalPrice(value:string|null):string|null{
  if(value===null)return null;
  ensure(/^[0-9]{1,12}(?:\.[0-9]{1,2})?$/.test(value));
  const [whole='0',fraction='']=value.split('.');
  const normalized=BigInt(whole).toString()+'.'+fraction.padEnd(2,'0');
  ensure(normalized!=='0.00');
  return normalized;
}
function money(value:unknown):string{const s=text(value);ensure(canonicalPrice(s)===s);return s;}
export function formatUSD(value:string|null):string{
  if(value===null)return 'Not entered';
  const [whole='0',fraction='00']=value.split('.');
  return '$'+whole.replace(/\B(?=(\d{3})+(?!\d))/g,',')+'.'+fraction;
}
const norm=(s:string)=>s.trim().toUpperCase().split(/\s+/).join(' ');
export function decode(value:unknown,request:Request):Result{
  const r=obj(value,['contract_version','source_kind','market','currency','asking_price_usd','asking_price_source','status','subject','comparables','selected_count','comparison_mode','provenance','valuation','price_per_sqft_supported','representative_coverage_verified']);
  ensure(r.contract_version===VERSION&&r.source_kind==='synthetic_fixture'&&r.market==='queens_11361_a2'&&r.currency==='USD'&&r.asking_price_source==='buyer_reported'&&r.comparison_mode==='current_snapshot'&&r.valuation===null&&r.price_per_sqft_supported===false&&r.representative_coverage_verified===false);
  const status=text(r.status) as Status;
  ensure(['supported','insufficient_data','ambiguous_address','out_of_coverage','evidence_unavailable'].includes(status));
  const asking=r.asking_price_usd===null?null:money(r.asking_price_usd);
  ensure(asking===canonicalPrice(request.asking_price_usd));
  const p=obj(r.provenance,['analysis_date','snapshot_publication_date','snapshot_version','area_source','sales_covered_from','sales_covered_through','lookback_fully_covered','source_revisions','publisher_attributed','sale_time_area_verified','historical_asof_verified','public_display_approved']);
  const cutoff=day(p.analysis_date),publication=day(p.snapshot_publication_date),from=day(p.sales_covered_from),through=day(p.sales_covered_through),version=text(p.snapshot_version);
  ensure(from<=through&&through<cutoff&&publication<=cutoff&&/^fixture-nyc-[a-z0-9-]{1,40}$/.test(version)&&p.area_source==='2'&&p.publisher_attributed===false&&p.sale_time_area_verified===false&&p.historical_asof_verified===false&&p.public_display_approved===false);
  const full=age(cutoff,from)>=365&&age(cutoff,through)===1;
  ensure(p.lookback_fully_covered===full);
  const revisions=obj(p.source_revisions,['usep-8jbt','64uk-42ks','bnx9-e6tj','8h5j-fqxa']);
  ensure(Object.values(revisions).every(v=>typeof v==='string'&&/^fixture-[a-z0-9-]{1,40}$/.test(v)));
  let subject:Subject|null=null;
  if(status==='supported'||status==='insufficient_data'){
    const s=obj(r.subject,['address','borough','zipcode','building_class','snapshot_gross_area_sqft']);
    const label=text(s.address);
    ensure(norm(label)===norm(request.address)&&norm(label).startsWith('FICTIONAL NYC ')&&s.borough==='Queens'&&s.zipcode==='11361'&&s.building_class==='A2');
    subject={address:label,snapshot_gross_area_sqft:num(s.snapshot_gross_area_sqft,1)};
  }else ensure(r.subject===null);
  ensure(Array.isArray(r.comparables)&&r.selected_count===r.comparables.length);
  ensure(status==='supported'?r.comparables.length>=3&&r.comparables.length<=5:r.comparables.length===0);
  const comparables=r.comparables.map((v:unknown,i:number):Comparable=>{
    const s=obj(v,['rank','sale_date','sale_price_usd','age_days','building_class','dof_neighbourhood','snapshot_gross_area_sqft','absolute_area_difference_sqft','selection_rule']);
    const sold=day(s.sale_date),days=num(s.age_days,1),area=num(s.snapshot_gross_area_sqft,1),diff=num(s.absolute_area_difference_sqft,0);
    ensure(subject&&s.rank===i+1&&sold>=from&&sold<=through&&days===age(cutoff,sold)&&days<=365&&s.building_class==='A2'&&s.dof_neighbourhood==='BAYSIDE'&&s.selection_rule==='earlier_whole_deed_same_snapshot_area_within_25_percent'&&diff===Math.abs(area-subject.snapshot_gross_area_sqft)&&diff*4<=subject.snapshot_gross_area_sqft);
    return {rank:i+1,sale_date:sold,sale_price_usd:money(s.sale_price_usd),age_days:days,snapshot_gross_area_sqft:area,absolute_area_difference_sqft:diff};
  });
  ensure(comparables.every((v,i)=>i===0||v.absolute_area_difference_sqft>=comparables[i-1]!.absolute_area_difference_sqft));
  return {status,subject,comparables,asking_price_usd:asking,analysis_date:cutoff,snapshot_publication_date:publication,snapshot_version:version,sales_covered_from:from,sales_covered_through:through,lookback_fully_covered:full};
}
