/**
 * MapLibre WebGL2 integration feasibility POC. The synthetic virtual coordinates
 * are intentionally not to scale or tied to real property/parcel coordinates.
 * All style layers and GeoJSON are inline. No tile provider, external style,
 * geocoder, API key, attribution claim or live property service is accessed.
 */
import { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import { diagramToVirtualLonLat, type ExampleSubject, type SaleId } from './data';

maplibregl.setWorkerUrl(workerUrl);

type Props = {
  subject: ExampleSubject;
  selectedSale: SaleId | null;
  onSelect: (sale: SaleId) => void;
};

type GeoPoint = { type: 'Point'; coordinates: [number, number] };
type DemoFeature = {
  type: 'Feature';
  id: number;
  geometry: GeoPoint;
  properties: { key: string; rank: number; kind: 'subject' | 'sale' };
};

const virtual = (x: number, y: number) => diagramToVirtualLonLat({ x, y });
const fictitiousRoads = [
  [[8, 29], [94, 29]], [[0, 70], [100, 70]],
  [[35, 0], [35, 100]], [[65, 0], [65, 100]],
].map((p, i) => ({
  type: 'Feature' as const, id: i, properties: {},
  geometry: { type: 'LineString' as const, coordinates: p.map(v => virtual(v[0] ?? 0, v[1] ?? 0)) },
}));
const fictitiousParks = [
  [[4, 4], [30, 4], [30, 22], [4, 22], [4, 4]],
  [[72, 82], [99, 82], [99, 99], [72, 99], [72, 82]],
].map((p, i) => ({
  type: 'Feature' as const, id: i, properties: {},
  geometry: { type: 'Polygon' as const, coordinates: [p.map(v => virtual(v[0] ?? 0, v[1] ?? 0))] },
}));

function makeStyle(subject: ExampleSubject): maplibregl.StyleSpecification {
  const points: DemoFeature[] = [
    { type: 'Feature', id: 99, geometry: { type: 'Point', coordinates: diagramToVirtualLonLat(subject.place) },
      properties: { key: 'subject', rank: 0, kind: 'subject' } },
    ...subject.sales.map((sale, index): DemoFeature => ({
      type: 'Feature', id: index + 1, geometry: { type: 'Point', coordinates: diagramToVirtualLonLat(sale.diagramPoint) },
      properties: { key: sale.id, rank: sale.rank, kind: 'sale' },
    })),
  ];
  // Data contracts are typed at this boundary, while MapLibre validates the
  // inline source/layer style at runtime. These coordinates are fictional.
  return {
    version: 8,
    sources: {
      'study-parks': { type: 'geojson', data: { type: 'FeatureCollection', features: fictitiousParks } },
      'study-roads': { type: 'geojson', data: { type: 'FeatureCollection', features: fictitiousRoads } },
      'study-points': { type: 'geojson', data: { type: 'FeatureCollection', features: points } },
    },
    layers: [
      { id: 'study-bg', type: 'background', paint: { 'background-color': '#e9efe7' } },
      { id: 'study-park-fill', type: 'fill', source: 'study-parks', paint: { 'fill-color': '#c4dac1', 'fill-opacity': 0.92 } },
      { id: 'study-road-outline', type: 'line', source: 'study-roads', paint: { 'line-color': '#ccd7c9', 'line-width': 34 } },
      { id: 'study-road', type: 'line', source: 'study-roads', paint: { 'line-color': '#fffefa', 'line-width': 28 } },
      { id: 'study-subject', type: 'circle', source: 'study-points',
        filter: ['==', ['get', 'kind'], 'subject'],
        paint: { 'circle-radius': 15, 'circle-color': '#fffefa', 'circle-stroke-color': '#255748', 'circle-stroke-width': 5 } },
      { id: 'study-sales', type: 'circle', source: 'study-points',
        filter: ['==', ['get', 'kind'], 'sale'],
        paint: { 'circle-radius': 12, 'circle-color': '#255748', 'circle-stroke-color': '#fff', 'circle-stroke-width': 3 } },
    ],
  };
}

export default function VectorMap({ subject, selectedSale, onSelect }: Props) {
  const node = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<maplibregl.Map | null>(null);
  const chooseRef = useRef(onSelect);
  const [status, setStatus] = useState<'mounting' | 'ready' | 'fallback'>('mounting');
  const [why, setWhy] = useState('');
  chooseRef.current = onSelect;

  useEffect(() => {
    const container = node.current;
    if (!container) return;
    try {
      const map = new maplibregl.Map({
        container,
        style: makeStyle(subject),
        center: [0, 0], zoom: 11.85,
        minZoom: 10.2, maxZoom: 14.6,
        renderWorldCopies: false, dragRotate: false, pitchWithRotate: false,
        scrollZoom: false, attributionControl: false,
        cooperativeGestures: true,
      });
      mapInstance.current = map;
      let settled = false;
      const showFallback = (reason: string) => {
        if (settled) return;
        settled = true;
        clearTimeout(loadGuard);
        setStatus('fallback');
        setWhy(reason);
      };
      // A worker that cannot fetch, lacks WebGL2 or crashes asynchronously
      // must not leave the buyer at a permanent "Preparing renderer" state.
      const loadGuard = window.setTimeout(() => showFallback(
        'The optional map renderer did not become ready. The evidence list remains available.'
      ), 6500);
      map.on('load', () => {
        if (settled) return;
        settled = true;
        clearTimeout(loadGuard);
        setStatus('ready');
      });
      map.on('error', () => showFallback(
        'The optional map renderer encountered a graphics or worker error. The evidence list remains available.'
      ));
      map.on('click', 'study-sales', event => {
        const key: unknown = event.features?.[0]?.properties?.key;
        if (key === 'c1' || key === 'c2' || key === 'c3') chooseRef.current(key);
      });
      map.on('mouseenter', 'study-sales', () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'study-sales', () => { map.getCanvas().style.cursor = ''; });
      return () => {
        settled = true;
        clearTimeout(loadGuard);
        mapInstance.current = null;
        map.remove();
      };
    } catch (err) {
      setStatus('fallback');
      setWhy(`The WebGL renderer could not start. ${err instanceof Error ? err.message : 'Rendering is unavailable.'}`);
      return;
    }
  }, [subject]);

  useEffect(() => {
    const map = mapInstance.current;
    if (!map || !map.isStyleLoaded()) return;
    map.setPaintProperty('study-sales', 'circle-color', [
      'case', ['==', ['get', 'key'], selectedSale ?? ''], '#dfaa5b', '#255748',
    ]);
    map.setPaintProperty('study-sales', 'circle-radius', [
      'case', ['==', ['get', 'key'], selectedSale ?? ''], 17, 12,
    ]);
  }, [selectedSale, status]);

  return <div className="vector-shell" data-testid="vector-renderer" aria-label="MapLibre WebGL virtual coordinate feasibility study">
    <div ref={node} className="maplibre-container" data-testid="maplibre-container" aria-hidden="true" />
    <div className="map-caption-floating">VECTOR RENDERER · VIRTUAL POSITIONS</div>
    {status === 'mounting' && <div className="render-indicator">Preparing local vector renderer…</div>}
    {status === 'fallback' && <div className="renderer-fallback" role="status" data-testid="webgl-fallback">
      <strong>Map unavailable</strong><p>{why}</p><span>Use the comparable list or switch to the SVG diagram.</span>
    </div>}
    {status === 'ready' && <div className="webgl-state" role="status" data-testid="webgl-ready">WebGL2 proof active · no tiles</div>}
    {status === 'ready' && <div className="map-zoom-controls"><button type="button" onClick={() => mapInstance.current?.zoomIn({ duration: 0 })} aria-label="Zoom in virtual map">+</button><button type="button" onClick={() => mapInstance.current?.zoomOut({ duration: 0 })} aria-label="Zoom out virtual map">−</button></div>}
    <div className="map-no-geo">No provider data · no real-world distances · conceptual only</div>
  </div>;
}
