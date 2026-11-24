import type {InvestigationView} from './evidenceBridge';

export type MapPoint = {rank:number;pin:string;coordinates:[number,number]};
export type MapEvidence = {source:string;digest:string;points:MapPoint[];reason:string|null};
const object=(v:unknown):Record<string,unknown>=>{
  if(!v||typeof v!=='object'||Array.isArray(v))throw Error('Invalid map response');
  return v as Record<string,unknown>;
};
export function adaptMap(raw:unknown, record:InvestigationView):MapEvidence {
  const r=object(raw);
  if(r.contract_version!=='synthetic-map-v1'||r.investigation_id!==record.investigationId||
     r.build_id!==record.sourceBuildId||r.source_kind!=='synthetic_fixture'||
     r.geometry_kind!=='virtual_display_point'||r.real_geography_verified!==false||
     r.distance_supported!==false||r.position_source_id!=='synthetic-display-geography-v1'||
     r.position_source_sha256!=='c692c4933f7e967c9bd89a5278126ffcbbda3fcbc5c37f4c0f1c6f2824d5f7b9')
    throw Error('Map provenance rejected');
  const collection=object(r.feature_collection);
  if(collection.type!=='FeatureCollection'||!Array.isArray(collection.features))
    throw Error('Invalid map collection');
  if(r.map_available===false){
    if(collection.features.length!==0||typeof r.reason!=='string'||
       !['map_disabled','geometry_unavailable','insufficient_or_unsupported_evidence'].includes(r.reason))
      throw Error('Invalid unavailable map');
    return {source:r.position_source_id,digest:r.position_source_sha256,points:[],reason:r.reason};
  }
  if(r.map_available!==true||r.reason!==null||record.selectedCount===0||
     !['supported_neighbourhood','exploratory_spatial'].includes(record.status)||
     collection.features.length!==record.selectedCount+1)throw Error('Map evidence count rejected');
  const seen=new Set<string>();
  const points=collection.features.map((item:unknown,rank:number):MapPoint=>{
    const f=object(item), p=object(f.properties), g=object(f.geometry);
    const pin=rank===0?record.subjectPin:record.comparables[rank-1]?.pin;
    if(!pin||f.type!=='Feature'||f.id!=='rank-'+rank||p.pin!==pin||p.rank!==rank||
       p.kind!==(rank===0?'subject':'comparable')||g.type!=='Point'||
       !Array.isArray(g.coordinates)||g.coordinates.length!==2||
       !g.coordinates.every((x:unknown)=>typeof x==='number'&&Number.isFinite(x)&&Math.abs(x)<=0.02))
      throw Error('Map identity or position rejected');
    const coordinates=g.coordinates as [number,number];
    const key=coordinates.join(',');
    if(seen.has(key))throw Error('Overlapping map positions rejected');
    seen.add(key);
    return {rank,pin,coordinates};
  });
  return {source:r.position_source_id,digest:r.position_source_sha256,points,reason:null};
}
