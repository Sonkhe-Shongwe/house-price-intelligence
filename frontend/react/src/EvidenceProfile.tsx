import './evidenceProfile.css';

/** Presentation only. Both service adapters keep their own wire validation.
 * No price inference, score, location, raw identifier or matching calculation.
 */
export type EvidenceFacts=Readonly<{rank:number;ageDays:number;areaDifferencePct:number}>;
export default function EvidenceProfile({facts}:{facts:EvidenceFacts}){
  const {rank,ageDays,areaDifferencePct}=facts;
  if(!Number.isInteger(rank)||rank<1||rank>5||!Number.isInteger(ageDays)||ageDays<1||ageDays>365||
     !Number.isFinite(areaDifferencePct)||areaDifferencePct<0||areaDifferencePct>25)return null;
  return <section className="ep-profile" data-testid="evidence-profile" aria-label={'Selected sale '+rank+' evidence profile'}>
    <div className="ep-heading"><span>Evidence profile / {String(rank).padStart(2,'0')}</span><small>Recorded facts</small></div>
    <div className="ep-grid">
      <div className="ep-metric"><h4>Sale recency</h4><strong data-testid="profile-age">{ageDays} <small>days earlier</small></strong>
        <svg viewBox="0 0 200 16" width="100%" height="16" aria-hidden="true" focusable="false">
          <rect width="200" height="8" y="4" className="ep-track"/>
          <rect width={ageDays/365*200} height="8" y="4" className="ep-fill"/>
          <line x1={ageDays/365*200} y1="0" x2={ageDays/365*200} y2="16" className="ep-tick"/>
        </svg><div className="ep-axis"><span>Analysis date</span><span>365 days earlier</span></div>
      </div>
      <div className="ep-metric"><h4>Area difference</h4><strong data-testid="profile-difference">{areaDifferencePct}%</strong>
        <svg viewBox="0 0 200 16" width="100%" height="16" aria-hidden="true" focusable="false">
          <rect width="200" height="8" y="4" className="ep-track"/>
          <rect width={areaDifferencePct/25*200} height="8" y="4" className="ep-fill"/>
          <line x1={areaDifferencePct/25*200} y1="0" x2={areaDifferencePct/25*200} y2="16" className="ep-tick"/>
        </svg><div className="ep-axis"><span>0%</span><span>25%</span></div>
      </div>
    </div>
    <p>Fixed display scales: 0–365 days and 0–25% area difference. These are evidence facts, not valuation confidence.</p>
  </section>;
}
