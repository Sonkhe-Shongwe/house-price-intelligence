/**
 * Deliberately invented study data. None of these are original SQL records,
 * backend contracts, geographic coordinates, genuine home prices or source claims.
 * 'x/y' are diagram placement percentages, not longitude/latitude or distances.
 */
export type EvidenceStatus = 'supported_neighbourhood' | 'insufficient_data';
export type SubjectId = 'a' | 'b';
export type SaleId = 'c1' | 'c2' | 'c3';
export type Point = { x: number; y: number };

export interface ExampleSale {
  id: SaleId;
  rank: number;
  label: string;
  priceText: string;
  date: string;
  buildingAreaText: string;
  diagramPoint: Point;
  reason: string;
}
export interface ExampleSubject {
  id: SubjectId;
  label: string;
  pinLabel: string;
  askingText: string;
  status: EvidenceStatus;
  place: Point;
  sales: ExampleSale[];
}

export const subjects: Record<SubjectId, ExampleSubject> = {
  a: {
    id: 'a', label: '101 Fictional Way', pinLabel: 'Fictional parcel A',
    askingText: '$500,000', status: 'supported_neighbourhood',
    place: { x: 51, y: 52 },
    sales: [
      { id: 'c1', rank: 1, label: '103 Fictional Way', priceText: '$525,000.01',
        date: '01 February 2024', buildingAreaText: '1,600 ft²',
        diagramPoint: { x: 25, y: 27 },
        reason: 'First invented earlier-sale example. The diagram position is not part of the selection rule.' },
      { id: 'c2', rank: 2, label: '108 Fictional Avenue', priceText: '$498,000.00',
        date: '01 February 2024', buildingAreaText: '1,600 ft²',
        diagramPoint: { x: 76, y: 28 },
        reason: 'Second invented completed-sale example. Its asking price is not being compared with a predicted value.' },
      { id: 'c3', rank: 3, label: '112 Fictional Lane', priceText: '$510,000.00',
        date: '01 February 2024', buildingAreaText: '1,600 ft²',
        diagramPoint: { x: 68, y: 77 },
        reason: 'Third invented earlier sale. Its map position is schematic, not a measured parcel location.' },
    ],
  },
  b: {
    id: 'b', label: '105 Fictional Court', pinLabel: 'Fictional parcel B',
    askingText: '$610,000', status: 'insufficient_data',
    place: { x: 72, y: 67 }, sales: [],
  },
};

/** Internal virtual renderer coordinates only. These are NOT property locations. */
export function diagramToVirtualLonLat(point: Point): [number, number] {
  return [(point.x - 50) * 0.0014, (50 - point.y) * 0.0014];
}
