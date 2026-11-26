import Icon from './Icon';
import {useEffect,useRef,useState} from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import type {MapPoint} from './mapEvidence';
import VirtualMapFallback from './VirtualMapFallback';
import atlasStyle from './mapStyles/atlas.json';
import terminalStyle from './mapStyles/terminal.json';
type MapTheme='atlas'|'terminal';
// These local style documents contain only empty GeoJSON and paint layers.
// Populate positions exclusively from the already validated map adapter.
function evidenceStyle(points:MapPoint[],theme:MapTheme):maplibregl.StyleSpecification{
  const style=structuredClone(theme==='atlas'?atlasStyle:terminalStyle) as unknown as maplibregl.StyleSpecification;
  style.sources.positions={type:'geojson',data:{type:'FeatureCollection',features:points.map(p=>({type:'Feature',id:p.rank,geometry:{type:'Point',coordinates:p.coordinates},properties:{rank:p.rank}}))}};
  return style;
}
maplibregl.setWorkerUrl(workerUrl);

export default function GeoVectorMap(props:{points:MapPoint[];selected:number|null;onSelect:(n:number)=>void}){
  const [theme,setTheme]=useState<MapTheme>('atlas');
  return <div className="geo-themed" data-map-theme={theme}>
    <div className="geo-style-controls" role="group" aria-label="Fictional map appearance">
      <button type="button" aria-pressed={theme==='atlas'} onClick={()=>setTheme('atlas')}>Atlas</button>
      <button type="button" aria-pressed={theme==='terminal'} onClick={()=>setTheme('terminal')}>Terminal</button>
    </div>
    <VectorCanvas key={theme} {...props} theme={theme}/>
    <div className="geo-legend"><span><i className="geo-legend-subject" aria-hidden="true"/>Subject</span><span><i className="geo-legend-sale" aria-hidden="true"/>Ranked sale</span><span><i className="geo-legend-selected" aria-hidden="true"/>Selected sale</span></div>
    <small>Selection halo is a screen-space highlight, not a geographic radius.</small>
  </div>;
}
function VectorCanvas({points,selected,onSelect,theme}:{points:MapPoint[];selected:number|null;onSelect:(n:number)=>void;theme:MapTheme}){
  const node=useRef<HTMLDivElement>(null);
  const instance=useRef<maplibregl.Map|null>(null);
  const buttons=useRef(new Map<number,HTMLButtonElement>());
  const releaseRenderer=useRef<(()=>void)|null>(null);
  const failureFocus=useRef(false),failureStatus=useRef<HTMLParagraphElement>(null);
  const choose=useRef(onSelect);choose.current=onSelect;
  const [status,setStatus]=useState<'loading'|'ready'|'fallback'>('loading');
  useEffect(()=>{
    if(!node.current)return;
    let map:maplibregl.Map|undefined;
    let disposed=false, failed=false;
    const markers:maplibregl.Marker[]=[];
    const fail=()=>{
      if(disposed||failed)return;
      failed=true;
      failureFocus.current=!!node.current?.contains(document.activeElement);
      setStatus('fallback');
    };
    const guard=window.setTimeout(fail,10000);
    const release=()=>{
      if(disposed)return;
      disposed=true;window.clearTimeout(guard);buttons.current.clear();
      markers.forEach(m=>m.remove());map?.remove();instance.current=null;
      if(releaseRenderer.current===release)releaseRenderer.current=null;
    };
    releaseRenderer.current=release;
    try{
      map=new maplibregl.Map({container:node.current,
        style:evidenceStyle(points,theme),
        center:[0,0],zoom:11.5,minZoom:9,maxZoom:16,renderWorldCopies:false,
        dragRotate:false,pitchWithRotate:false,scrollZoom:false,cooperativeGestures:true,attributionControl:false});
      instance.current=map;
      map.touchZoomRotate.disableRotation();
      const active=map;
      active.on('error',fail);
      active.on('webglcontextlost',fail);
      active.on('load',()=>{
        if(disposed||failed)return;
        try{
          const bounds=new maplibregl.LngLatBounds();
          for(const point of points){
            bounds.extend(point.coordinates);
            const element=document.createElement(point.rank===0?'div':'button');
            element.className='geo-marker '+(point.rank===0?'geo-subject':'geo-sale');
            element.textContent=point.rank===0?'S':String(point.rank);
            element.setAttribute('data-testid','geo-pin-'+point.rank);
            if(element instanceof HTMLButtonElement){
              element.type='button';
              element.setAttribute('aria-label','Select comparable '+point.rank);
              element.setAttribute('aria-pressed','false');
              element.addEventListener('click',()=>choose.current(point.rank));
              buttons.current.set(point.rank,element);
            }else element.setAttribute('aria-label','Subject fictional parcel');
            markers.push(new maplibregl.Marker({element}).setLngLat(point.coordinates).addTo(active));
          }
          active.fitBounds(bounds,{padding:48,maxZoom:14,duration:0});
          window.clearTimeout(guard);setStatus('ready');
        }catch{fail();}
      });
    }catch{fail();}
    return release;
  },[points]);
  useEffect(()=>{
    if(status!=='fallback')return;
    releaseRenderer.current?.();
    if(failureFocus.current)failureStatus.current?.focus();
  },[status]);
  useEffect(()=>{
    buttons.current.forEach((b,rank)=>b.setAttribute('aria-pressed',String(rank===selected)));
    if(status==='ready'){
      const map=instance.current;
      if(map?.getSource('positions'))for(const point of points){
        map.setFeatureState({source:'positions',id:point.rank},{selected:point.rank!==0&&point.rank===selected});
      }
    }
  },[selected,status,points]);
  function resetView(){
    const map=instance.current;if(!map||status!=='ready')return;
    const bounds=new maplibregl.LngLatBounds();points.forEach(p=>bounds.extend(p.coordinates));
    map.fitBounds(bounds,{padding:48,maxZoom:14,duration:0});
  }
  return <div className="geo-vector" data-testid="geo-vector">
    <div className="geo-canvas" ref={node} hidden={status==='fallback'} aria-label="Virtual display coordinates"/>
    {status==='loading'&&<p role="status">Preparing local vector renderer…</p>}
    {status==='fallback'&&<><p ref={failureStatus} tabIndex={-1} data-testid="geo-fallback" role="status">Interactive map unavailable. The verified sale list remains usable.</p><VirtualMapFallback points={points} selected={selected} onSelect={onSelect}/></>}
    {status==='ready'&&<><p data-testid="geo-ready" role="status">Virtual map · No basemap · Not to scale</p><p className="geo-gesture-help">On touch screens, use two fingers to move the map. Sale buttons and the lightweight view remain available.</p>
      <div className="geo-controls"><button type="button" aria-label="Zoom in fictional map" onClick={()=>instance.current?.zoomIn({duration:0})}><Icon name="plus" size={20}/></button>
      <button type="button" aria-label="Zoom out fictional map" onClick={()=>instance.current?.zoomOut({duration:0})}><Icon name="minus" size={20}/></button><button type="button" aria-label="Reset fictional map view" onClick={resetView}><Icon name="refresh"/> Reset view</button></div></>}
  </div>;
}

/** Separate opt-in, generated contextual fixture. Never receives buyer records or markers. */
export function ContextualAtlasPreview(){
  const node=useRef<HTMLDivElement>(null),instance=useRef<maplibregl.Map|null>(null);
  const [status,setStatus]=useState<'idle'|'loading'|'ready'|'failed'>('idle');
  useEffect(()=>{
    if(status!=='loading'||!node.current)return;
    const container=node.current;
    let disposed=false,failed=false,protocolAdded=false;
    const lifetime=new AbortController();
    const url=new URL('/context/atlas-fixture-v1.pmtiles',window.location.origin).href;
    let map:maplibregl.Map|undefined;
    const cleanup=()=>{
      lifetime.abort();window.clearTimeout(guard);
      map?.remove();map=undefined;instance.current=null;
      if(protocolAdded){maplibregl.removeProtocol('pmtiles');protocolAdded=false;}
    };
    const fail=()=>{
      if(disposed||failed)return;
      failed=true;cleanup();setStatus('failed');
    };
    const guard=window.setTimeout(fail,15000);
    void (async()=>{
      try{
        const {PMTiles,Protocol}=await import('pmtiles');
        const head=await fetch(url,{method:'HEAD',cache:'no-store',redirect:'error',signal:lifetime.signal});
        const length=Number(head.headers.get('content-length')),etag=head.headers.get('etag');
        if(!head.ok||head.headers.get('x-context-transport-fixture')!=='true'
            ||!Number.isSafeInteger(length)||length<16384||length>50*1024**2
            ||!etag||!/^"[0-9a-f]{64}"$/.test(etag))throw Error('fixture unavailable');
        const source={
          getKey:()=>url,
          getBytes:async(offset:number,count:number,signal?:AbortSignal,expected?:string)=>{
            if(lifetime.signal.aborted||!Number.isSafeInteger(offset)||!Number.isSafeInteger(count)
                ||offset<0||count<1||count>8*1024**2||offset+count>length
                ||(expected&&expected!==etag))throw Error('fixture range rejected');
            const combined=signal?AbortSignal.any([signal,lifetime.signal]):lifetime.signal;
            const response=await fetch(url,{headers:{Range:`bytes=${offset}-${offset+count-1}`,'If-Match':etag},
              cache:'no-store',redirect:'error',signal:combined});
            if(response.status!==206||response.headers.get('etag')!==etag
                ||response.headers.get('content-range')!==`bytes ${offset}-${offset+count-1}/${length}`
                ||Number(response.headers.get('content-length'))!==count
                ||response.headers.get('x-context-transport-fixture')!=='true')throw Error('fixture response rejected');
            const data=await response.arrayBuffer();
            if(data.byteLength!==count)throw Error('fixture length mismatch');
            return {data,etag};
          }
        };
        const archive=new PMTiles(source);
        const header=await archive.getHeader();
        if(header.specVersion!==3||header.minZoom!==0||header.maxZoom!==0||header.tileType!==1
            ||header.numAddressedTiles!==1)throw Error('fixture format rejected');
        if(disposed||failed)return;
        const protocol=new Protocol();
        protocol.add(archive);
        const prefix='pmtiles://'+url;
        maplibregl.addProtocol('pmtiles',(params,abort)=>{
          const suffix=params.url.slice(prefix.length);
          if(!params.url.startsWith(prefix)||!(suffix===''||/^\/[0-9]+\/[0-9]+\/[0-9]+$/.test(suffix)))
            return Promise.reject(Error('unapproved context URL'));
          return protocol.tile(params,abort);
        });
        protocolAdded=true;
        map=new maplibregl.Map({container,center:[0,0],zoom:0.7,minZoom:0,maxZoom:2,
          renderWorldCopies:false,dragRotate:false,pitchWithRotate:false,scrollZoom:false,
          cooperativeGestures:true,attributionControl:false,style:{version:8,
            sources:{context:{type:'vector',url:prefix}},
            layers:[{id:'context-paper',type:'background',paint:{'background-color':'#f0eee4'}},
              {id:'context-water',type:'fill',source:'context','source-layer':'water',paint:{'fill-color':'#a6c4cf'}},
              {id:'context-park',type:'fill',source:'context','source-layer':'landuse',paint:{'fill-color':'#bfd1b1'}},
              {id:'context-road',type:'line',source:'context','source-layer':'roads',paint:{'line-color':'#a74429','line-width':3}}]}});
        instance.current=map;map.touchZoomRotate.disableRotation();
        map.on('error',fail);map.on('webglcontextlost',fail);
        map.once('idle',()=>{
          if(disposed||failed)return;
          if(!map?.queryRenderedFeatures({layers:['context-water','context-park','context-road']}).length){fail();return;}
          window.clearTimeout(guard);setStatus('ready');
        });
      }catch{fail();}
    })();
    return ()=>{disposed=true;cleanup();};
  // Keep the map mounted when the readiness state changes.
  },[status==='idle']);
  return <main className="context-preview" data-testid="context-preview">
    <a href="/">Return to research workspace</a>
    <p className="hpi-eyebrow">ATLAS / LOCAL QUALIFICATION</p>
    <h1>Contextual vector map test</h1>
    <p role="note">Invented geometry, not real geographic context. No property markers, addresses, distances or historical claims.</p>
    {status==='idle'&&<button type="button" className="geo-load" data-testid="context-load" onClick={()=>setStatus('loading')}>Load invented contextual map</button>}
    <div ref={node} className="geo-canvas" hidden={status==='idle'||status==='failed'} aria-label="Invented contextual vector map"/>
    {status==='loading'&&<p role="status">Decoding local qualification archive…</p>}
    {status==='ready'&&<><p role="status" data-testid="context-ready">Invented PMTiles vector layers rendered locally</p>
      <div className="geo-controls"><button type="button" onClick={()=>instance.current?.zoomIn({duration:0})}>Zoom in</button>
      <button type="button" onClick={()=>instance.current?.zoomOut({duration:0})}>Zoom out</button>
      <button type="button" onClick={()=>instance.current?.jumpTo({center:[0,0],zoom:0.7})}>Reset view</button></div></>}
    {status==='failed'&&<p role="alert" data-testid="context-unavailable">Contextual map unavailable. No geographic inference is made.</p>}
    <p>Generated fixture only. No OpenStreetMap or other external geographic data loaded.</p>
  </main>;
}
