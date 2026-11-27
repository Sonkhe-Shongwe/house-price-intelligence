/** Display-only explanations derived from the validated frozen fictional result. */
import type {Result,Comparable} from './saInvestigationContract';

export function evidenceExplanation(result:Result):{reason:string;next:string}{
  switch(result.reason){
    case 'primary_window':return {reason:'At least three distinct earlier fictional properties qualified within 365 days.',next:'Review the extent differences and sale dates; record questions for further investigation. Do not infer a current market value.'};
    case 'extended_window':return {reason:'Fewer than three qualified within 365 days; the window expanded to 730 days.',next:'Review the older sale dates and extent differences before relying on the historical comparison. Do not infer a current market value.'};
    case 'subject_identity_unresolved':return {reason:'The selected fictional parcel cannot be resolved exactly.',next:'Confirm the parcel identity before comparing sale evidence.'};
    case 'subject_attributes_or_location_unqualified':return {reason:'Dated extent or location evidence is insufficient.',next:'Seek dated dwelling and land extents and qualified location evidence before comparing.'};
    case 'unsupported_fixture_class_or_locality':return {reason:'The property is outside this fictional study scope.',next:'Use evidence qualified for the relevant property class and locality; do not generalise this study.'};
    case 'fewer_than_three_qualified_fixture_parcels':return {reason:'Fewer than three distinct earlier properties qualify.',next:'Seek additional eligible historical evidence rather than relaxing the matching rules or inventing an estimate.'};
    default:return {reason:'Insufficient fictional evidence.',next:'Resolve the evidence limitation before comparing.'};
  }
}

// Contract extents have at most six decimal places and <=1,000,000 m².
// Integer millionths retain exact displayed differences, without float drift.
function millionths(value:string):number{
  const [whole,fraction='']=value.split('.');
  return Number(whole)*1_000_000+Number(fraction.padEnd(6,'0'));
}
export function extentDifference(subject:string|undefined,comparable:string):string{
  if(subject===undefined)return 'Unknown';
  const delta=millionths(comparable)-millionths(subject);
  if(delta===0)return 'Same extent';
  const absolute=Math.abs(delta);
  const fractional=String(absolute%1_000_000).padStart(6,'0').replace(/0+$/,'');
  return String(Math.floor(absolute/1_000_000))+(fractional?'.'+fractional:'')+' m² '+(delta>0?'larger':'smaller');
}
export function comparableDifferences(result:Result,sale:Comparable):string{
  return 'Dwelling: '+extentDifference(result.subject.dwelling_extent,sale.dwelling_extent)+'; land: '+extentDifference(result.subject.land_extent,sale.land_extent)+'.';
}
export function evidenceModeLimit(result:Result):string{
  return result.mode==='retrospective'?'Retrospective only; historical availability is not established.':
    result.fictional_as_of_qualified?'Fictional as-of qualification only; no real historical availability verified.':
    'Fictional as-of qualification not established.';
}
