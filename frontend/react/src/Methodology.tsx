export default function Methodology(){
  return <section className="hpi-methodology" data-testid="methodology"><div className="hpi-page-heading"><div>
    <p className="hpi-eyebrow">EVIDENCE &amp; LIMITATIONS</p><h1>How the evidence works.</h1>
    <p>Understand what the application knows, what it does not know, and how it preserves a decision trail.</p></div></div>
    <div className="hpi-method-grid">
      <article><small>01 / IDENTITY</small><h2>Parcel, not a confirmed building</h2><p>A fictional street label can identify multiple parcels. Choose one explicitly. Building identity remains unverified.</p></article>
      <article><small>02 / MATCHING</small><h2>Earlier sales only</h2><p>The Python matcher applies date, class, township, area and neighbourhood rules. Prices do not select comparables. Spatial fallback is exploratory, not a valuation.</p></article>
      <article><small>03 / MONEY</small><h2>Separate asking and sale prices</h2><p>Asking price and entered area are buyer-reported. Recorded fixture sale prices use exact USD cents. No current price or prediction interval is produced.</p></article>
      <article><small>04 / PROVENANCE</small><h2>Frozen investigation evidence</h2><p>Reopening verifies the saved response, source snapshots, transaction identity and sale cents. Notes are stored separately and remain editable.</p></article>
      <article><small>05 / GEOGRAPHY</small><h2>Virtual map only</h2><p>The optional map uses independently versioned synthetic display positions, not real parcel geometry or distances. The map cannot change matching rules.</p></article>
      <article><small>06 / COVERAGE &amp; PRIVACY</small><h2>Local fictional fixture</h2><p>Only township 17 and class 203 are supported in this demonstration. Historical source availability and publisher display rights are unverified. No accounts or production security. Never enter personal data. Persistence requires an explicit fixture database file.</p></article>
    </div></section>;
}
