/**
 * Source-bound, read-only presentation adapter for the current v0.3 HPI API.
 * This candidate does NOT calculate comparables, valuations or map coordinates.
 * For a genuine API investigation, there is NO verified geometry available.
 */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const PIN = /^[0-9]{14}$/;
const EXACT_USD = /^(?:0|[1-9][0-9]*)\.[0-9]{2}$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

export type ActualStatus = 'supported_neighbourhood' | 'exploratory_spatial' |
  'insufficient_data' | 'out_of_coverage';
export type UnavailableLocation = Readonly<{available:false;reason:'no_verified_map_feature_contract'}>;
export type ComparableView = {
  uiKey:string; rank:number; pin:string; document:string; saleDate:string;
  exactPriceUsd:string; priceText:string; explanation:string;
};
export type InvestigationView = {
  investigationId:string; contractVersion:'p3-draft-v0.3';
  status:ActualStatus; reason:string|null; tier:string; analysisDate:string;
  subjectLabel:string; subjectPin:string|null; askingPriceText:string;
  selectedCount:number; comparables:ComparableView[]; warnings:string[];
  sourceBuildId:string; sourceSnapshotIds:string[]; valuation:null;
  buildingIdentityVerified:false; location:UnavailableLocation;
};
export type ShortlistView = {
  shortlistId:string; label:string; maxEntries:3;
  entries:Array<{investigationId:string;noteText:string;matchPolicyVersion:string;investigation:InvestigationView}>;
};
export class EvidenceBridgeError extends Error {
  constructor(public readonly code:string){
    super('HPI source contract rejected: '+code);
    this.name='EvidenceBridgeError';
  }
}
const fail=(code:string):never=>{throw new EvidenceBridgeError(code);};
function obj(value:unknown,code:string):Record<string,unknown>{
  return value && typeof value==='object' && !Array.isArray(value) ?
    value as Record<string,unknown> : fail(code);
}
function txt(v:unknown,code:string):string{
  return typeof v==='string' && v.length>0 ? v : fail(code);
}
function guid(v:unknown,code:string):string{
  return typeof v==='string' && UUID.test(v) ? v : fail(code);
}
function iso(v:unknown,code:string):string{
  if(typeof v!=='string'||!DATE.test(v))fail(code);
  const dt=new Date(v+'T00:00:00Z');
  return Number.isFinite(dt.getTime()) && dt.toISOString().slice(0,10)===v ? v:fail(code);
}
function money(v:unknown,code:string):string{
  return typeof v==='string' && EXACT_USD.test(v)?v:fail(code);
}
export function formatExactUsd(v:string):string{
  const [d,c]=money(v,'invalid_exact_usd').split('.');
  return '$'+BigInt(d!).toLocaleString('en-US')+'.'+c;
}
const STATUSES:ReadonlySet<string>=new Set([
  'supported_neighbourhood','exploratory_spatial','insufficient_data','out_of_coverage'
]);
export function adaptInvestigation(payload:unknown):InvestigationView{
  const raw=obj(payload,'invalid_investigation');
  if(raw.contract_version!=='p3-draft-v0.3')fail('unsupported_contract');
  const investigationId=guid(raw.investigation_id,'invalid_investigation_id');
  if(raw.valuation!==null)fail('unexpected_valuation');
  if(!STATUSES.has(String(raw.status)))fail('unknown_status');
  const status=raw.status as ActualStatus;
  const build=obj(raw.data_build,'missing_build');
  if(build.source_kind!=='synthetic_fixture')fail('non_fixture_source');
  const sourceBuildId=txt(build.build_id,'missing_build_id');
  if(!Array.isArray(build.source_snapshot_ids)||
     !build.source_snapshot_ids.every(s=>typeof s==='string'&&s.length>0)){
    fail('missing_source_snapshots');
  }
  const sourceSnapshotIds=[...(build.source_snapshot_ids as string[])];
  const subject=obj(raw.subject,'missing_subject');
  const subjectPin=subject.pin===null ? null :
    typeof subject.pin==='string'&&PIN.test(subject.pin)?subject.pin:fail('invalid_subject_pin');
  if(subject.address_id!==undefined &&
     (subject.identity_scope!=='parcel_only' ||
      subject.identity_status!=='synthetic_mapping_only' ||
      subject.building_identity_verified!==false))fail('unverified_address_identity');
  const askingPriceText=subject.asking_price_usd===null?'Not supplied':
    formatExactUsd(money(subject.asking_price_usd,'invalid_asking_price'));
  const count=raw.selected_count;
  if(typeof count!=='number'||!Number.isInteger(count)||count<0||count>3){
    fail('invalid_selected_count');
  }
  const rawComparables=raw.comparables;
  if(!Array.isArray(rawComparables)||rawComparables.length!==count){
    fail('comparable_count_mismatch');
  }
  const rawWarnings=raw.warnings;
  if(!Array.isArray(rawWarnings)||!rawWarnings.every(w=>typeof w==='string')){
    fail('invalid_warnings');
  }
  const seen=new Set<string>();
  const comparables=(rawComparables as unknown[]).map((itemUnknown:unknown,index:number):ComparableView=>{
    const item=obj(itemUnknown,'invalid_comparable');
    if(Object.hasOwn(item,'sale_price'))fail('legacy_float_price');
    const pin=txt(item.pin,'invalid_sale_pin');
    if(!PIN.test(pin))fail('invalid_sale_pin');
    const document=txt(item.document,'invalid_sale_document');
    const saleDate=iso(item.sale_date,'invalid_sale_date');
    const key=pin+'|'+document+'|'+saleDate;
    if(seen.has(key))fail('duplicate_sale_identity');
    seen.add(key);
    const exactPriceUsd=money(item.sale_price_usd,'invalid_sale_money');
    return {uiKey:investigationId+':ui-rank:'+(index+1),rank:index+1,pin,document,
      saleDate,exactPriceUsd,priceText:formatExactUsd(exactPriceUsd),
      explanation:txt(item.explanation,'missing_sale_explanation')};
  });
  const reason=raw.reason===null?null:
    typeof raw.reason==='string'?raw.reason:fail('invalid_reason');
  const tier=txt(raw.tier,'invalid_tier');
  if(status==='supported_neighbourhood'&&tier!=='same_neighborhood')fail('invalid_supported_tier');
  if(status==='exploratory_spatial'&&tier!=='spatial_fallback')fail('invalid_exploratory_tier');
  if(status==='out_of_coverage'&&count!==0)fail('out_of_scope_sale_count');
  const subjectLabel=subject.label===null||subject.label===undefined?
    'Unlabelled fictional parcel':txt(subject.label,'invalid_subject_label');
  return {investigationId,contractVersion:'p3-draft-v0.3',status,reason,tier,
    analysisDate:iso(raw.analysis_date,'invalid_analysis_date'),subjectLabel,subjectPin,
    askingPriceText,selectedCount:count as number,comparables,warnings:[...(rawWarnings as string[])],
    sourceBuildId,sourceSnapshotIds,valuation:null,buildingIdentityVerified:false,
    location:{available:false,reason:'no_verified_map_feature_contract'}};
}
export function adaptShortlist(payload:unknown):ShortlistView{
  const raw=obj(payload,'invalid_shortlist');
  if(raw.source_kind!=='synthetic_fixture')fail('non_fixture_shortlist');
  const shortlistId=guid(raw.shortlist_id,'invalid_shortlist_id');
  if(raw.max_entries!==3)fail('unexpected_shortlist_limit');
  const rawEntries=raw.entries;
  if(!Array.isArray(rawEntries)||rawEntries.length>3)fail('invalid_shortlist_entries');
  const entries=(rawEntries as unknown[]).map((unk:unknown)=>{
    const e=obj(unk,'invalid_shortlist_entry');
    const investigationId=guid(e.investigation_id,'invalid_member_id');
    const investigation=adaptInvestigation(e.investigation);
    if(investigation.investigationId!==investigationId)fail('member_identity_mismatch');
    if(typeof e.note_text!=='string'||e.note_text.length>800)fail('invalid_note');
    return {investigationId,noteText:e.note_text,
      matchPolicyVersion:txt(e.match_policy_version,'missing_policy_version'),investigation};
  });
  if(new Set(entries.map(e=>e.investigationId)).size!==entries.length)fail('duplicate_members');
  return {shortlistId,label:txt(raw.label,'missing_shortlist_label'),maxEntries:3,entries};
}
