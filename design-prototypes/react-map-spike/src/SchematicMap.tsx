import type { ExampleSubject, SaleId } from './data';

type Props = {
  subject: ExampleSubject;
  selectedSale: SaleId | null;
  onSelect: (id: SaleId) => void;
};

export default function SchematicMap({ subject, selectedSale, onSelect }: Props) {
  return <div className="map-stage schematic-stage" data-testid="schematic-map" aria-label="Not-to-scale schematic district diagram">
    <svg className="district-illustration" viewBox="0 0 820 510" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <rect width="820" height="510" fill="#e8eee6" />
      <path d="M-10 13L197 2L196 168L35 188Z M650 324L835 284L836 519L637 516Z M368 4L460 9L454 126L364 113Z" fill="#c5dcc3" />
      <path d="M45 40Q120 21 147 93Q147 148 87 166Q24 141 45 40Z" fill="#b2d7dd" />
      <g stroke="#fafbf8" fill="#d9e1d7" strokeWidth="2">
        <path d="M220 13L327 6L320 134L217 131Z"/><path d="M350 16L464 24L461 142L340 129Z"/>
        <path d="M493 24L615 8L631 138L480 145Z"/><path d="M219 251L339 242L332 335L218 331Z"/>
        <path d="M359 253L465 239L468 338L360 339Z"/><path d="M482 251L611 239L624 339L482 342Z"/>
        <path d="M221 359L332 351L328 492L217 492Z"/><path d="M349 358L466 355L459 487L352 487Z"/>
        <path d="M487 355L616 350L627 487L489 488Z"/>
      </g>
      <g fill="#c5ccc1" stroke="#bcc5b9" strokeWidth="1.5">
        <rect x="246" y="42" width="42" height="39" rx="3"/><rect x="374" y="51" width="51" height="38" rx="3"/>
        <rect x="526" y="52" width="57" height="39" rx="3"/><rect x="245" y="265" width="55" height="35" rx="3"/>
        <rect x="389" y="270" width="44" height="43" rx="3"/><rect x="525" y="264" width="59" height="40" rx="3"/>
        <rect x="246" y="400" width="55" height="43" rx="3"/><rect x="383" y="392" width="47" height="50" rx="3"/>
        <rect x="534" y="396" width="49" height="40" rx="3"/>
      </g>
      <g fill="none" strokeLinecap="round">
        <path stroke="#c3cec1" strokeWidth="61" d="M169 -10L175 520M452 -10L460 520M-10 201L830 194M-10 344L830 340M676 -10L690 520"/>
        <path stroke="#fbfaf5" strokeWidth="51" d="M169 -10L175 520M452 -10L460 520M-10 201L830 194M-10 344L830 340M676 -10L690 520"/>
      </g>
      <g fontFamily="system-ui,sans-serif" fontWeight="750" fontSize="12" letterSpacing="2" fill="#77887a">
        <text x="260" y="179">HERITAGE AVENUE</text><text x="272" y="326">GARDEN LANE</text>
        <text x="438" y="127" transform="rotate(-90 438 127)">MARKET WALK</text>
        <text x="18" y="487" fontSize="13">THE FICTIONAL DISTRICT · NOT TO SCALE</text>
      </g>
    </svg>
    <div className="map-caption-floating">SCHEMATIC · NOT GEOGRAPHIC</div>
    <div className="map-north" aria-hidden="true">N ↑</div>
    <span className="diagram-pin subject-pin" style={{ left: `${subject.place.x}%`, top: `${subject.place.y}%` }} aria-label={`Subject ${subject.label}`}>⌂</span>
    {subject.sales.map(sale => <button
      type="button" key={sale.id}
      className={`diagram-pin comparable-pin ${selectedSale === sale.id ? 'is-selected' : ''}`}
      style={{ left: `${sale.diagramPoint.x}%`, top: `${sale.diagramPoint.y}%` }}
      onClick={() => onSelect(sale.id)}
      aria-label={`Select fictional comparable ${sale.rank}, ${sale.label}, ${sale.priceText}`}
      aria-pressed={selectedSale === sale.id}
      data-testid={`schematic-pin-${sale.id}`}
    >{sale.rank}</button>)}
    {!subject.sales.length && <div className="no-geometry"><b>No eligible sales to plot</b><span>Absence of evidence is not a valuation.</span></div>}
  </div>;
}
