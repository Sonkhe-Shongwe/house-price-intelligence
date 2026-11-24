import {useEffect,useRef,useState} from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import type {MapPoint} from './mapEvidence';
maplibregl.setWorkerUrl(workerUrl);

export default function GeoVectorMap({points,selected,onSelect}:{points:MapPoint[];selected:number|null;onSelect:(n:number)=>void}){
  const node=useRef<HTMLDivElement>(null);
  const instance=useRef<maplibregl.Map|null>(null);
  const buttons=useRef(new Map<number,HTMLButtonElement>());
  const choose=useRef(onSelect);choose.current=onSelect;
  const [status,setStatus]=useState<'loading'|'ready'|'fallback'>('loading');
  useEffect(()=>{
    if(!node.current)return;
    let map:maplibregl.Map|undefined;
    let disposed=false, failed=false;
    const markers:maplibregl.Marker[]=[];
    const fail=()=>{if(!disposed){failed=true;setStatus('fallback');}};
    const guard=window.setTimeout(fail,10000);
    try{
      map=new maplibregl.Map({container:node.current,
        style:{version:8,sources:{positions:{type:'geojson',data:{type:'FeatureCollection',
          features:points.map(p=>({type:'Feature',id:p.rank,geometry:{type:'Point',coordinates:p.coordinates},
            properties:{rank:p.rank}}))}}},
          layers:[{id:'virtual-background',type:'background',paint:{'background-color':'#e4eee7'}},
            {id:'virtual-position-halos',type:'circle',source:'positions',
              paint:{'circle-radius':25,'circle-color':'#245648','circle-opacity':0.10}}]},
        center:[0,0],zoom:11.5,minZoom:9,maxZoom:16,renderWorldCopies:false,
        dragRotate:false,pitchWithRotate:false,scrollZoom:false,attributionControl:false});
      instance.current=map;
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
    return ()=>{disposed=true;window.clearTimeout(guard);buttons.current.clear();
      markers.forEach(m=>m.remove());map?.remove();instance.current=null;};
  },[points]);
  useEffect(()=>{
    buttons.current.forEach((b,rank)=>b.setAttribute('aria-pressed',String(rank===selected)));
  },[selected,status]);
  return <div className="geo-vector" data-testid="geo-vector">
    <div className="geo-canvas" ref={node} hidden={status==='fallback'} aria-label="Virtual display coordinates"/>
    {status==='loading'&&<p role="status">Preparing local vector renderer…</p>}
    {status==='fallback'&&<p data-testid="geo-fallback" role="status">Map unavailable. The verified sale list remains usable.</p>}
    {status==='ready'&&<><p data-testid="geo-ready" role="status">Virtual map · No basemap · Not to scale</p>
      <div className="geo-controls"><button type="button" aria-label="Zoom in fictional map" onClick={()=>instance.current?.zoomIn({duration:0})}>+</button>
      <button type="button" aria-label="Zoom out fictional map" onClick={()=>instance.current?.zoomOut({duration:0})}>−</button></div></>}
  </div>;
}
