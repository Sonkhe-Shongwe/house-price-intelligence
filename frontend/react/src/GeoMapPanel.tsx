import Icon from './Icon';
import {Component,lazy,Suspense,useEffect,useRef,useState,type ReactNode} from 'react';
import {adaptMap,type MapEvidence} from './mapEvidence';
import type {InvestigationView} from './evidenceBridge';
import './geoMap.css';
import CentroidPreview from './CentroidPreview';
const VectorMap=lazy(()=>import('./GeoVectorMap'));
class OptionalMapBoundary extends Component<{children:ReactNode},{failed:boolean}>{
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed
    ? <p role="status" data-testid="geo-bundle-fallback">Optional map could not load. The verified sale list remains usable.</p>
    :this.props.children;}
}
export default function GeoMapPanel({record,selected,onSelect}:{record:InvestigationView;selected:number|null;onSelect:(n:number)=>void}){
  const [data,setData]=useState<MapEvidence|null>(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  async function load(){
    controller.current?.abort();
    const c=new AbortController();controller.current=c;
    setData(null);setError('');setBusy(true);
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
    <header><small>FICTIONAL GEOGRAPHIC EVIDENCE</small><h3>Explore saved sale positions.</h3>
      <p>Virtual points only. No streets, real locations, distances or valuation.</p></header>
    <OptionalMapBoundary><Suspense fallback={<p role="status">Loading optional map renderer…</p>}>
      <VectorMap points={data.points} selected={selected} onSelect={onSelect}/>
    </Suspense></OptionalMapBoundary>
    <small className="geo-provenance">Display source: {data.source} · SHA-256 {data.digest.slice(0,12)} · Separate from original matching coordinates</small>
  </article><CentroidPreview record={record} selected={selected} onSelect={onSelect}/></div>;
  return <div className="geo-evidence-stack"><article className="buyer-map-disabled" data-testid="buyer-no-geometry"><div className="buyer-disabled-icon" aria-hidden="true"><Icon name="map" size={32}/></div>
    <span>REAL GEOLOCATION EVIDENCE / NOT AVAILABLE</span><h3>Map withheld.</h3>
    <p>Real geographic coordinates remain unverified. The optional fictional display layer does not alter saved comparable evidence.</p>
    <button type="button" className="geo-load" data-testid="geo-load" disabled={busy} onClick={()=>void load()}><Icon name="map"/>{busy?'Verifying map…':'Explore fictional map'}</button>
    {error&&<p role="alert" data-testid="geo-error">{error}</p>}
    {data?.reason&&<p role="status" data-testid="geo-unavailable">{data.reason==='map_disabled'?'Fictional map mode is not enabled.': 'No verified fictional display points for this result.'}</p>}
    <strong>NO REAL MAP MARKERS · NO VALUATION</strong>
  </article><CentroidPreview record={record} selected={selected} onSelect={onSelect}/></div>;
}
