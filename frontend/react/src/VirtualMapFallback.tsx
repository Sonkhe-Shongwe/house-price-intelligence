import Icon from './Icon';
import {ActionButton} from './UI';
import type {MapPoint} from './mapEvidence';

/** A local non-WebGL view of already validated virtual display points.
 * Not source-shaped centroids, a physical map, geographic scale or distance.
 * Never call this component with unverified, withheld or insufficient geometry.
 */
export default function VirtualMapFallback({points,selected,onSelect}:{points:MapPoint[];selected:number|null;onSelect:(rank:number)=>void}){
  if(!points.length)return null;
  const origin=points[0]!.coordinates;
  const offsets=points.map(p=>({rank:p.rank,x:p.coordinates[0]-origin[0],y:p.coordinates[1]-origin[1]}));
  const extent=Math.max(0.000001,...offsets.flatMap(p=>[Math.abs(p.x),Math.abs(p.y)]));
  const sales=offsets.filter(p=>p.rank>0);
  return <section className="geo-static" data-testid="geo-static-fallback" aria-label="Virtual position schematic">
    <h4><Icon name="map"/> Virtual position schematic</h4>
    <p>Same verified fictional display points, shown without the interactive renderer. No real locations, basemap, distance scale or valuation.</p>
    <svg viewBox="0 0 280 240" width="100%" role="img" aria-label="Fictional display points relative to the subject, numbered in original sale order">
      <rect x="4" y="4" width="272" height="232" rx="4" fill="#eeeee4" stroke="#a7b5a4"/>
      <path d="M140 16V224M16 120H264" stroke="#788a7c" strokeDasharray="4 4"/>
      {offsets.map(p=>{
        const x=140+p.x/extent*96,y=120-p.y/extent*86;
        const active=p.rank!==0&&p.rank===selected;
        return <g key={p.rank} data-testid={'geo-static-point-'+p.rank} data-selected={active}>
          {active&&<circle cx={x} cy={y} r="16" fill="none" stroke="#a74429" strokeWidth="2"/>}
          {p.rank===0?<rect x={x-11} y={y-11} width="22" height="22" rx="2" fill="#254b3a"/>:<circle cx={x} cy={y} r="11" fill={active?'#a74429':'#faf8f2'} stroke="#254b3a" strokeWidth="1.5"/>}
          <text x={x} y={y+4} textAnchor="middle" fontSize="12" fontWeight="650" fill={active||p.rank===0?'white':'#254b3a'}>{p.rank===0?'S':p.rank}</text>
        </g>;
      })}
    </svg>
    <p className="geo-static-legend">S = subject. Numbers = original sale ranks. Highlight marks selection only.</p>
    <div className="geo-static-actions" role="group" aria-label="Select comparable in virtual schematic">
      {sales.map(p=><ActionButton key={p.rank} icon="parcel" aria-pressed={selected===p.rank} data-testid={'geo-static-rank-'+p.rank} onClick={()=>onSelect(p.rank)}>Sale {p.rank}</ActionButton>)}
    </div>
  </section>;
}
