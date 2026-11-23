'use strict';

// Synthetic fixture-only browser experience. No real property API, maps, or model.
// All source-derived and user-entered content is inserted with textContent.
(() => {
  const id = (name) => document.getElementById(name);
  const form = id('investigation-form');
  const feedback = id('form-feedback');
  const submit = id('submit-button');
  const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  let lastInvestigation = null;
  let addressSearchRevision = 0;
  let addressSelectionRevision = 0;
  let selectedAddressId = null;

  function text(node, value) { node.textContent = value == null ? '' : String(value); }
  function element(tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content != null) text(node, content);
    return node;
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
  function setFeedback(message, success = false) {
    feedback.className = success ? 'form-feedback success' : 'form-feedback';
    text(feedback, message);
  }
  function state(value, label, kind = '') {
    const target = id('result-state');
    target.className = 'result-state' + (kind ? ' ' + kind : '');
    text(target, label);
  }
  function currencyAmount(value) {
    // Canonical decimal strings only; BigInt handles whole-dollar grouping.
    if (typeof value !== 'string' || !/^(?:0|[1-9][0-9]*)\.[0-9]{2}$/.test(value))
      return 'Not available';
    const [whole, cents] = value.split('.');
    return '$' + BigInt(whole).toLocaleString('en-US') + '.' + cents;
  }
  function niceDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return 'Unknown date';
    const [year, month, day] = value.split('-');
    return `${day}/${month}/${year}`;
  }
  function explainReason(reason) {
    const known = {
      'parcel_identity_not_resolved':'The parcel identifier was not provided. The enquiry was saved without matching.',
      'parcel_not_found_in_curated_build':'That PIN is not present in the invented evidence build.',
      'unsupported_market_or_class':'Only the demonstration market (Township 17, Class 203) is supported.',
      'resolved_property_out_of_scope':'The stored parcel is outside the research scope.',
      'no_eligible_prior_sales':'There are no earlier sales meeting the eligibility rules.',
      'insufficient_local_and_nearby_sales':'Fewer than three eligible earlier sales were available.',
      'missing_subject_coordinates':'The verified parcel location is insufficient for geographic matching.'
    };
    return known[reason] || 'There is not enough eligible evidence to support this investigation.';
  }
  function setHash(value) {
    history.replaceState(null, '', '#investigation/' + value);
  }

  function render(data) {
    if (data?.data_build?.source_kind !== 'synthetic_fixture') throw Error('This page accepts only synthetic fixture responses.');
    if (!uuid.test(data.investigation_id)) throw Error('The server returned an invalid investigation identifier.');
    if (data.valuation !== null) throw Error('Unexpected valuation data; refusing to display response.');
    if (data.contract_version !== 'p3-draft-v0.3') throw Error('Unsupported synthetic money contract.');
    lastInvestigation = data.investigation_id;
    id('result-empty').hidden = true;
    id('result-content').hidden = false;
    state(data.status, 'EVIDENCE LOADED', 'complete');
    text(id('result-title'), data.subject?.label || 'Property investigation');
    text(id('result-subtitle'), 'Synthetic parcel ' + (data.subject?.pin || 'unresolved') + ' · User asking ' + currencyAmount(data.subject?.asking_price_usd));
    const statuses = {
      'supported_neighbourhood':['Same-neighbourhood evidence',''],
      'exploratory_spatial':['Exploratory nearby sales','warning'],
      'insufficient_data':['Insufficient evidence','unavailable'],
      'out_of_coverage':['Outside test coverage','unavailable']
    };
    const [description, style] = statuses[data.status] || ['Unverified result', 'unavailable'];
    id('status-pill').className = 'status-pill' + (style ? ' ' + style : '');
    text(id('status-pill'), description);
    text(id('stat-count'), data.selected_count ?? 0);
    const tier = data.tier === 'same_neighborhood' ? 'Neighbourhood' : data.tier === 'spatial_fallback' ? '2 km fallback' : 'None';
    text(id('stat-tier'), tier);
    text(id('stat-date'), niceDate(data.analysis_date));
    const warns = id('warnings'); clear(warns);
    for (const message of (Array.isArray(data.warnings) ? data.warnings : [])) {
      warns.appendChild(element('div', data.status === 'exploratory_spatial' ? 'warning' : 'warning muted', message));
    }
    text(id('comps-count'), `${data.selected_count ?? 0} selected · recorded-sale fixtures`);
    const rows = id('comparables'); clear(rows);
    const comps = Array.isArray(data.comparables) ? data.comparables : [];
    for (const [index, comp] of comps.entries()) {
      const card = element('article', 'comp');
      const top = element('div', 'comp-top');
      const left = element('div');
      left.appendChild(element('div', 'comp-label', `COMPARABLE ${String(index + 1).padStart(2, '0')}`));
      if (Object.hasOwn(comp, 'sale_price') || typeof comp.sale_price_usd !== 'string'
          || !/^(?:0|[1-9][0-9]*)\.[0-9]{2}$/.test(comp.sale_price_usd))
        throw Error('Invalid exact-money comparable evidence.');
      left.appendChild(element('div', 'comp-price', currencyAmount(comp.sale_price_usd)));
      top.appendChild(left);
      top.appendChild(element('div', 'comp-tag', comp.same_neighborhood ? 'Same neighbourhood' : 'Nearby sale'));
      card.appendChild(top);
      card.appendChild(element('p', 'comp-explain', comp.explanation || 'Synthetic comparable evidence'));
      const facts = element('div', 'comp-data');
      facts.appendChild(element('span', '', niceDate(comp.sale_date)));
      facts.appendChild(element('span', '', `${comp.size_difference_pct ?? '?'}% size diff`));
      facts.appendChild(element('span', '', `${comp.age_days ?? '?'} days earlier`));
      if (comp.distance_km != null) facts.appendChild(element('span', '', `${comp.distance_km} km away`));
      card.appendChild(facts);
      rows.appendChild(card);
    }
    const empty = id('unsupported');
    empty.hidden = comps.length > 0;
    if (!comps.length) text(empty, explainReason(data.reason) + ' No comparable sale prices or numerical valuation have been produced.');
    const provenance = id('provenance-content'); clear(provenance);
    const lines = [
      ['Fixture build', data.data_build.build_id],
      ['Build time', data.data_build.built_at_utc],
      ['Source snapshots', (data.data_build.source_snapshot_ids || []).join(', ')],
      ['Result contract', data.contract_version],
      ['Evidence status', data.status],
      ['Independent historic point-in-time verification', 'No'],
      ['Approved public record display', 'No'],
      ['Valuation', 'Not produced']
    ];
    for (const [key, val] of lines) provenance.appendChild(element('p', '', key + ': ' + (val ?? 'unknown')));
    id('reopen-id').value = data.investigation_id;
    setHash(data.investigation_id);
  }

  function handleError(error, messagePrefix) {
    console.error(messagePrefix, error);
    setFeedback(messagePrefix + ': ' + (error?.message || 'Unknown error'));
    state('error', 'REQUEST FAILED');
  }

  async function requestJson(url, options) {
    const response = await fetch(url, {cache:'no-store', credentials:'same-origin', ...options});
    let body;
    try { body = await response.json(); } catch { throw Error('The local API returned invalid JSON.'); }
    if (!response.ok) {
      if (body?.field && body?.code) throw Error(`${body.field}: ${body.code}`);
      throw Error(body?.error || `HTTP ${response.status}`);
    }
    return body;
  }

  // Search returns only possible fictional addresses, never an inferred PIN.
  // A second request resolves an explicitly selected address ID server-side.
  const addressForm = id('address-search-form');
  const addressResults = id('address-results');
  const addressFeedback = id('address-search-feedback');
  const selectedAddress = id('selected-address');
  const addressButton = id('address-search-button');
  function resetAddressSelection() {
    addressSelectionRevision += 1;
    selectedAddressId = null;
    selectedAddress.hidden = true;
    text(selectedAddress, '');
  }
  id('pin').addEventListener('input', resetAddressSelection);
  id('address-query').addEventListener('input', () => {
    ++addressSearchRevision;
    resetAddressSelection();
    id('pin').value = '';
    clear(addressResults);
    addressResults.hidden = true;
    text(addressFeedback, 'Search the new fictional address before selecting a parcel.');
  });

  addressForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = id('address-query').value.trim();
    const revision = ++addressSearchRevision;
    resetAddressSelection();
    id('pin').value = ''; // Do not silently investigate a previous subject.
    clear(addressResults);
    addressResults.hidden = true;
    addressButton.disabled = true;
    text(addressFeedback, 'Searching fictional addresses…');
    try {
      const response = await requestJson('/v1/addresses/search', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({query})
      });
      if (revision !== addressSearchRevision) return;
      if (response?.source_kind !== 'synthetic_fixture' || !Array.isArray(response.candidates)) {
        throw Error('Unexpected address source. No property was selected.');
      }
      if (response.candidates.length === 0) {
        text(addressFeedback, 'No invented address matched. Try Fictional Way or enter a synthetic PIN.');
        return;
      }
      text(addressFeedback, response.candidates.length + ' fictional address option(s). Select one. No automatic identity guess.');
      for (const candidate of response.candidates) {
        if (typeof candidate.address_id !== 'string' || typeof candidate.display_address !== 'string') {
          throw Error('Address search returned an invalid candidate.');
        }
        const option = element('button', 'address-option', candidate.display_address);
        option.type = 'button';
        option.addEventListener('click', async () => {
          const selectionRevision = ++addressSelectionRevision;
          text(addressFeedback, 'Resolving the selected fictional address…');
          try {
            const resolved = await requestJson('/v1/addresses/' + encodeURIComponent(candidate.address_id));
            if (selectionRevision !== addressSelectionRevision || revision !== addressSearchRevision) return;
            if (resolved?.source_kind !== 'synthetic_fixture'
                || resolved?.identity_status !== 'synthetic_mapping_only'
                || resolved.address_id !== candidate.address_id
                || !/^\d{14}$/.test(resolved.pin)) {
              throw Error('The selected address did not resolve to a synthetic parcel.');
            }
            selectedAddressId = resolved.address_id;
            id('pin').value = resolved.pin;
            id('label').value = resolved.display_address.slice(0, 120);
            selectedAddress.hidden = false;
            text(selectedAddress, 'Selected: ' + resolved.display_address + ' (fictional address)');
            text(addressFeedback, 'Property selected. Review your inputs and investigate.');
            clear(addressResults);
            addressResults.hidden = true;
          } catch (error) {
            if (selectionRevision === addressSelectionRevision)
              text(addressFeedback, 'Could not select fictional address: ' + error.message);
          }
        });
        addressResults.appendChild(option);
      }
      addressResults.hidden = false;
    } catch (error) {
      if (revision === addressSearchRevision) text(addressFeedback, 'Address search failed: ' + error.message);
    } finally { if (revision === addressSearchRevision) addressButton.disabled = false; }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const pin = id('pin').value.trim();
    if (!/^\d{14}$/.test(pin)) { setFeedback('Parcel PIN must contain exactly 14 digits.'); return; }
    const rawPrice = id('price').value.trim();
    if (rawPrice && !/^\d+(?:\.\d{1,2})?$/.test(rawPrice)) { setFeedback('Enter the asking price using up to two decimal places.'); return; }
    const area = Number(id('area').value);
    if (!Number.isFinite(area) || area <= 0 || area > 100000) { setFeedback('Enter a valid positive building area.'); return; }
    const subject = {
      pin, building_area_sqft:area, asking_price_usd:rawPrice || null,
      label:id('label').value.trim() || null
    };
    if (selectedAddressId !== null) subject.address_id = selectedAddressId;
    const payload = {
      township_code:'17', class_code:'203', analysis_date:id('analysis-date').value,
      subject
    };
    submit.disabled = true; setFeedback('Creating a synthetic investigation…', true);
    state('loading', 'ANALYSING…');
    try {
      const result = await requestJson('/v1/investigations', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      render(result);
      setFeedback('Investigation saved in the temporary synthetic workspace.', true);
    } catch (error) { handleError(error, 'Could not investigate property'); }
    finally { submit.disabled = false; }
  });

  async function reopen(uid) {
    if (!uuid.test(uid)) { setFeedback('Provide a valid lowercase investigation UUID.'); return; }
    setFeedback('Loading saved investigation…', true);
    try {
      const result = await requestJson('/v1/investigations/' + uid);
      render(result);
      setFeedback('Saved investigation reopened without rerunning matching.', true);
    } catch (error) { handleError(error, 'Could not open saved result'); }
  }

  id('reopen-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    await reopen(id('reopen-id').value.trim());
  });
  id('example-known').addEventListener('click', () => { resetAddressSelection(); id('pin').value = '00000000000001'; id('area').value = '1600'; id('price').value = '500000.00'; id('label').value = 'My example property'; id('analysis-date').value = '2024-07-01'; setFeedback('Known invented parcel loaded.', true); });
  id('example-unknown').addEventListener('click', () => { resetAddressSelection(); id('pin').value = '00000000000099'; id('area').value = '1600'; id('price').value = '500000.00'; id('label').value = 'Unknown synthetic parcel'; id('analysis-date').value = '2024-07-01'; setFeedback('Unknown parcel loaded. Submit to observe an abstention.', true); });
  id('copy-link').addEventListener('click', async () => {
    if (!lastInvestigation) return;
    try {
      await navigator.clipboard.writeText(window.location.href);
      setFeedback('Investigation link copied. Available only while this local server runs.', true);
    } catch { setFeedback('Copy your browser URL to reopen this investigation in the current session.', true); }
  });
  const starting = window.location.hash.match(/^#investigation\/([0-9a-f-]+)$/);
  if (starting) reopen(starting[1]);
})();
