import {ActionButton} from './UI';
import './evidenceNavigation.css';

/** Navigate existing server order; no ranking or writes. */
export function EvidenceNavigation({ranks,selected,onSelect}:{ranks:readonly number[];selected:number|null;onSelect:(rank:number)=>void}){
  if(!ranks.length)return null;
  const index=selected===null?-1:ranks.indexOf(selected);
  const previous=index>0, next=index<ranks.length-1;
  return <div className="hpi-evidence-navigation" role="group" aria-label="Comparable evidence navigation" data-testid="evidence-navigation">
    <ActionButton icon="previous" aria-disabled={!previous} onClick={()=>{if(previous)onSelect(ranks[index-1]!);}} data-testid="evidence-previous">Previous sale</ActionButton>
    <p role="status" aria-atomic="true" data-testid="evidence-position">{index<0?'Choose a sale':`Sale ${index+1} of ${ranks.length}`}</p>
    <ActionButton icon="next" aria-disabled={!next} onClick={()=>{if(next)onSelect(ranks[index+1]!);}} data-testid="evidence-next">Next sale</ActionButton>
  </div>;
}

/** Explicit focus transfer; no automatic scroll or extra server request. */
export function EvidenceJump({targetId}:{targetId:string}){
  return <ActionButton icon="down" aria-controls={targetId} onClick={()=>document.getElementById(targetId)?.focus()} data-testid="evidence-jump">Go to saved evidence</ActionButton>;
}
