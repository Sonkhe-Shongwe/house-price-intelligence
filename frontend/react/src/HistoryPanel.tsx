import {ActionButton,PageHeading,StatusMessage,EmptyState,LoadingState} from './UI';
import {useEffect,useState} from 'react';
import {adaptHistory,type HistoryIndex,type ActualStatus} from './evidenceBridge';
export const evidenceLabel=(s:ActualStatus)=>({supported_neighbourhood:'Neighbourhood evidence',
  exploratory_spatial:'Exploratory evidence',insufficient_data:'Insufficient evidence',
  out_of_coverage:'Outside coverage'})[s];

type Props={mode:'home'|'saved';revision:number;onOpen:(id:string)=>void;onNew:()=>void;
  onCompare:()=>void;onHistory:()=>void;disabled:boolean};
export default function HistoryPanel({mode,revision,onOpen,onNew,onCompare,onHistory,disabled}:Props){
  const [data,setData]=useState<HistoryIndex|null>(null);
  const [error,setError]=useState('');
  const [refresh,setRefresh]=useState(0);
  const [query,setQuery]=useState('');
  const [filter,setFilter]=useState('all');
  useEffect(()=>{
    const controller=new AbortController();
    setData(null);setError('');
    (async()=>{
      try{
        const r=await fetch('/v1/investigations/history',{signal:controller.signal,cache:'no-store',credentials:'same-origin'});
        if(!r.ok)throw Error('History unavailable');
        const verified=adaptHistory(await r.json());
        if(!controller.signal.aborted)setData(verified);
      }catch{if(!controller.signal.aborted)setError('Saved history could not be verified. Retry or open a known saved ID in Investigate.');}
    })();
    return ()=>controller.abort();
  },[revision,refresh,mode]);
  const rows=(data?.items??[]).filter(i=>mode==='home'||(
    (filter==='all'||filter===i.status)&&[i.label,i.pin??'',i.analysisDate].some(x=>x.toLowerCase().includes(query.trim().toLowerCase()))));
  return <section className="hpi-history" data-testid="history-panel">
    <PageHeading eyebrow={mode==='home'?'BUYER WORKSPACE':'YOUR RESEARCH LIBRARY'} title={mode==='home'?'Make an informed choice.':'Saved investigations'} description={mode==='home'?'Investigate earlier sales, preserve evidence and compare the properties you are considering.':'Reopen frozen evidence from your current local database. Search the latest 30 enquiries.'} action={<ActionButton className="hpi-primary" type="button" disabled={disabled} onClick={onNew} data-testid="workspace-new-investigation" icon="plus" variant="primary">New investigation</ActionButton>}/>
    {mode==='home'&&<div className="hpi-home-grid">
      <article className="hpi-metric"><small>RECENT SAVED INVESTIGATIONS</small><strong>{data?data.items.length+(data.truncated?'+':''):'—'}</strong><p>Verified in the current fixture database</p></article>
      <article className="hpi-metric"><small>YOUR NEXT DECISION</small><h2>Compare properties</h2><p>Resume an existing shortlist or create one with up to three properties.</p>
      <ActionButton type="button" onClick={onCompare} icon="compare" variant="secondary">Open comparison workspace</ActionButton></article>
      <article className="hpi-metric"><small>DATA BOUNDARY</small><h2>Fictional only</h2><p>Recorded sale fixtures, no real addresses, no current value estimate.</p></article>
    </div>}
    <div className="hpi-history-card"><div className="hpi-history-heading"><div><h2>{mode==='home'?'Recent investigations':'Investigation library'}</h2>
      <p>Earlier completed sales, not live listings or valuations.</p></div><ActionButton type="button" onClick={()=>setRefresh(n=>n+1)} data-testid="history-refresh" icon="refresh" variant="secondary">Refresh</ActionButton></div>
      {mode==='saved'&&<div className="hpi-history-filters"><label>Search address, parcel or analysis date<input data-testid="history-search" value={query} onChange={e=>setQuery(e.target.value)} maxLength={120}/></label>
        <label>Evidence status<select value={filter} data-testid="history-status-filter" onChange={e=>setFilter(e.target.value)}>
          <option value="all">All statuses</option><option value="supported_neighbourhood">Neighbourhood evidence</option><option value="exploratory_spatial">Exploratory evidence</option><option value="insufficient_data">Insufficient evidence</option><option value="out_of_coverage">Outside coverage</option>
        </select></label></div>}
      {error&&<StatusMessage tone="error" data-testid="history-error">{error}</StatusMessage>}
      {!data&&!error&&<LoadingState>Verifying saved investigations…</LoadingState>}
      {data&&rows.length===0&&<EmptyState className="hpi-empty" data-testid="history-empty">{data.items.length?'No investigations match these filters.':'No saved investigations yet. Start with a fictional parcel.'}</EmptyState>}
      {data&&<ul className="hpi-history-list" data-testid="history-list">{rows.slice(0,mode==='home'?3:30).map(item=><li key={item.id}>
        <div><strong>{item.label}</strong><small>Parcel {item.pin??'unresolved'} · Analysis {item.analysisDate}</small></div>
        <div><span className="hpi-evidence-status">{evidenceLabel(item.status)}</span><small>{item.count} earlier sales · Asking {item.askingPriceText}</small></div>
        <ActionButton type="button" data-testid="history-open" disabled={disabled} onClick={()=>onOpen(item.id)} icon="open" variant="secondary">Open evidence</ActionButton>
      </li>)}</ul>}
      {data?.truncated&&<p className="hpi-history-limit">Showing the latest 30 investigations. Older saved IDs can still be reopened in Investigate.</p>}
      {mode==='home'&&<ActionButton type="button" onClick={onHistory} icon="saved" variant="secondary">View saved investigations</ActionButton>}
    </div>
  </section>;
}
