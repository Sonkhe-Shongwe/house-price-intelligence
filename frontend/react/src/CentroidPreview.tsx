import {useEffect,useRef,useState} from 'react';
import type {InvestigationView} from './evidenceBridge';
import {fixtureFetch} from './fixtureFetch';

type Point={rank:number;assessment_year:number;offset_x:number;offset_y:number};
type Result={points:Point[];reason:string|null};
const reasons=['unsupported_fixture_revision','insufficient_evidence','missing_geometry','overlapping_centroids','outside_schematic_extent'];
function exact(v:unknown,keys:string):Record<string,unknown>{
  if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).sort().join(' ')!==keys.split(' ').sort().join(' '))throw Error('Invalid centroid fields');
  return v as Record<string,unknown>;
}
function adapt(raw:unknown,record:InvestigationView):Result{
  const r=exact(raw,'contract_version investigation_id build_id source_kind geometry_kind building_identity_verified real_geography_verified public_display_approved historical_asof_verified distance_supported source_snapshot_id available reason points');
  if(r.contract_version!=='centroid-preview-v1'||r.investigation_id!==record.investigationId||r.build_id!==record.sourceBuildId
    ||r.source_kind!=='synthetic_fixture'||r.geometry_kind!=='fictional_parcel_centroid_schematic'
    ||r.building_identity_verified!==false||r.real_geography_verified!==false||r.public_display_approved!==false
    ||r.historical_asof_verified!==false||r.distance_supported!==false||!Array.isArray(r.points))throw Error('Untrusted centroid response');
  const sourceOk=typeof r.source_snapshot_id==='string'&&record.sourceSnapshotIds.includes(r.source_snapshot_id)&&r.source_snapshot_id.startsWith('fixture-geography-');
  if(r.available===false){
    if(r.points.length||typeof r.reason!=='string'||!reasons.includes(r.reason)
      ||(r.reason==='unsupported_fixture_revision'?r.source_snapshot_id!==null:!sourceOk))throw Error('Invalid withheld geometry');
    return {points:[],reason:r.reason};
  }
  if(r.available!==true||r.reason!==null||!sourceOk||record.selectedCount<3||r.points.length!==record.selectedCount+1)throw Error('Invalid centroid coverage');
  const seen=new Set<string>();
  const points=r.points.map((item:unknown,i:number)=>{
    const p=exact(item,'rank assessment_year offset_x offset_y');
    const year=Number((i===0?record.analysisDate:record.comparables[i-1]!.saleDate).slice(0,4))-1;
    if(p.rank!==i||p.assessment_year!==year||typeof p.offset_x!=='number'||typeof p.offset_y!=='number'
      ||!Number.isInteger(p.offset_x)||!Number.isInteger(p.offset_y)||Math.abs(p.offset_x)>20||Math.abs(p.offset_y)>20
      ||(i===0&&(p.offset_x!==0||p.offset_y!==0)))throw Error('Invalid centroid identity');
    const key=p.offset_x+','+p.offset_y;if(seen.has(key))throw Error('Overlapping centroids');seen.add(key);
    return p as Point;
  });
  return {points,reason:null};
}
export default function CentroidPreview({record,selected,onSelect}:{record:InvestigationView;selected:number|null;onSelect:(n:number)=>void}){
  const [result,setResult]=useState<Result|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(false);
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  async function load(){
    controller.current?.abort();const c=new AbortController();controller.current=c;
    setBusy(true);setError(false);setResult(null);
    try{
      const res=await fixtureFetch('/v1/investigations/'+record.investigationId+'/centroid-preview',{signal:c.signal});
      if(!res.ok)throw Error('Unavailable');
      const value=adapt(await res.json(),record);if(!c.signal.aborted)setResult(value);
    }catch{if(!c.signal.aborted)setError(true);}
    finally{if(!c.signal.aborted)setBusy(false);}
  }
  const extent=Math.max(1,...(result?.points??[]).flatMap(p=>[Math.abs(p.offset_x),Math.abs(p.offset_y)]));
  return <section className="hpi-provenance" aria-label="Fictional parcel centroid rehearsal">
    <h3>Source-shaped centroid evidence</h3><p>Fictional assessor-style parcel centroids, not building locations. Relative schematic only; no basemap, geographic coordinates, distance scale or valuation.</p>
    <button type="button" data-testid="centroid-load" disabled={busy} onClick={()=>void load()}>{busy?'Checking centroids…':'View centroid rehearsal'}</button>
    {error&&<p role="alert" data-testid="centroid-error">Centroid evidence could not be verified. Saved sales remain available.</p>}
    {result?.reason&&<p role="status" data-testid="centroid-unavailable">{result.reason==='overlapping_centroids'?'Centroids overlap at schematic precision. No invented separation is shown.':'No complete reviewed centroid schematic for this investigation.'}</p>}
    {result&&result.points.length>0&&<div data-testid="centroid-ready">
      <svg viewBox="0 0 280 250" width="100%" role="img" aria-label="Relative fictional centroid diagram with subject at centre and numbered comparables">
        <rect x="4" y="4" width="272" height="242" rx="10" fill="#e4eee7"/>
        <path d="M140 18V232M18 125H262" stroke="#718778" strokeDasharray="4 4"/>
        {result.points.map(p=>{const x=140+p.offset_x/extent*96,y=125-p.offset_y/extent*88;
          return <g key={p.rank}><circle cx={x} cy={y} r="12" fill={p.rank===0?'#223c32':p.rank===selected?'#8b461e':'#38634e'}/>
            <text x={x} y={y+4} textAnchor="middle" fontSize="12" fill="white">{p.rank===0?'S':p.rank}</text></g>;})}
      </svg>
      <p>Subject and {record.selectedCount} earlier sales, in original server order.</p>
      <div className="geo-controls">{result.points.filter(p=>p.rank>0).map(p=><button key={p.rank} type="button" data-testid={'centroid-rank-'+p.rank} aria-pressed={selected===p.rank} onClick={()=>onSelect(p.rank)}>Sale {p.rank}</button>)}</div>
    </div>}
  </section>;
}
