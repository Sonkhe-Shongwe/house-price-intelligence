import Icon from './Icon';
import {Component,lazy,Suspense,useEffect,useRef,useState,type ReactNode} from 'react';
import {adaptMap,type MapEvidence} from './mapEvidence';
import type {InvestigationView} from './evidenceBridge';
import './geoMap.css';
import CentroidPreview from './CentroidPreview';
import VirtualMapFallback from './VirtualMapFallback';
const VectorMap=lazy(()=>import('./GeoVectorMap'));
type DisplayMode='interactive'|'schematic';
class OptionalMapBoundary extends Component<{children:ReactNode;fallback:ReactNode},{failed:boolean}>{
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed
    ? <><p role="status" data-testid="geo-bundle-fallback">Optional map could not load. The verified sale list remains usable.</p>{this.props.fallback}</>
    :this.props.children;}
}
export default function GeoMapPanel({record,selected,onSelect}:{record:InvestigationView;selected:number|null;onSelect:(n:number)=>void}){
  const [data,setData]=useState<MapEvidence|null>(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [mode,setMode]=useState<DisplayMode>('interactive');
  const mapHeading=useRef<HTMLHeadingElement>(null);
  const activeSale=record.comparables.find(s=>s.rank===selected);
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  useEffect(()=>{if(data?.points.length)mapHeading.current?.focus();},[data]);
  async function load(nextMode:DisplayMode){
    controller.current?.abort();
    const c=new AbortController();controller.current=c;
    setMode(nextMode);setData(null);setError('');setBusy(true);
    try{
      const response=await fetch('/v1/investigations/'+record.investigationId+'/map',
        {signal:c.signal,credentials:'same-origin',cache:'no-store'});
      if(!response.ok)throw Error('Source geography unavailable');
      const adapted=adaptMap(await response.json(),record);
      if(!c.signal.aborted)setData(adapted);
    }catch{if(!c.signal.aborted)setError('Map evidence could not be verified. Use the saved sale list.');}
    finally{if(!c.signal.aborted)setBusy(false);}
  }
  if(data&&data.points.length>0)return <div className="geo-evidence-stack"><article className="geo-panel" data-testid="geo-panel">
    <header><small>FICTIONAL GEOGRAPHIC EVIDENCE</small><h3 ref={mapHeading} tabIndex={-1}>Explore saved sale positions.</h3>
      <p>Virtual points only. No streets, real locations, distances or valuation.</p></header>
    <div className="geo-display-choice" role="group" aria-label="Virtual evidence display">
      <button type="button" data-testid="geo-mode-interactive" aria-pressed={mode==='interactive'} onClick={()=>setMode('interactive')}><Icon name="map"/>Interactive map</button>
      <button type="button" data-testid="geo-mode-schematic" aria-pressed={mode==='schematic'} onClick={()=>setMode('schematic')}><Icon name="parcel"/>Lightweight schematic</button>
    </div>
    {mode==='schematic'?<VirtualMapFallback points={data.points} selected={selected} onSelect={onSelect}/>:<OptionalMapBoundary fallback={<VirtualMapFallback points={data.points} selected={selected} onSelect={onSelect}/>}><Suspense fallback={<p role="status">Loading optional map renderer…</p>}>
      <VectorMap points={data.points} selected={selected} onSelect={onSelect}/>
    </Suspense></OptionalMapBoundary>}
    <div className="geo-selected-sale" role="status" aria-live="polite" data-testid="geo-selected-sale">
      {activeSale?<><small>SELECTED EARLIER SALE · {activeSale.rank} OF {record.selectedCount}</small><strong>{activeSale.priceText}</strong><span>{activeSale.saleDate} · Completed sale, not a valuation</span></>:<p>Choose a numbered sale to inspect its original completed-sale price and date.</p>}
    </div>
    <small className="geo-provenance">Display source: {data.source} · SHA-256 {data.digest.slice(0,12)} · Separate from original matching coordinates</small>
  </article><CentroidPreview record={record} selected={selected} onSelect={onSelect}/></div>;
  return <div className="geo-evidence-stack"><article className="buyer-map-disabled" data-testid="buyer-no-geometry"><div className="buyer-disabled-icon" aria-hidden="true"><Icon name="map" size={32}/></div>
    <span>REAL GEOLOCATION EVIDENCE / NOT AVAILABLE</span><h3>Map withheld.</h3>
    <p>Real geographic coordinates remain unverified. The optional fictional display layer does not alter saved comparable evidence.</p>
    <div className="geo-display-choice">
      <button type="button" className="geo-load" data-testid="geo-load" disabled={busy} onClick={()=>void load('interactive')}><Icon name="map"/>{busy&&mode==='interactive'?'Verifying map…':'Explore fictional map'}</button>
      <button type="button" className="geo-load" data-testid="geo-load-schematic" disabled={busy} onClick={()=>void load('schematic')}><Icon name="parcel"/>{busy&&mode==='schematic'?'Verifying positions…':'View lightweight schematic'}</button>
    </div>
    {error&&<p role="alert" data-testid="geo-error">{error}</p>}
    {data?.reason&&<p role="status" data-testid="geo-unavailable">{data.reason==='map_disabled'?'Fictional map mode is not enabled.': 'No verified fictional display points for this result.'}</p>}
    <strong>NO REAL MAP MARKERS · NO VALUATION</strong>
  </article><CentroidPreview record={record} selected={selected} onSelect={onSelect}/></div>;
}
