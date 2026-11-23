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
      const hasSharedAddress = response.candidates.some(item => item.ambiguous_address);
      text(addressFeedback, response.candidates.length + ' fictional parcel candidate(s). '
        + (hasSharedAddress ? 'One address has multiple parcels: choose the correct option. ' : '')
        + 'No automatic identity guess.');
      for (const candidate of response.candidates) {
        if (typeof candidate.address_id !== 'string' || typeof candidate.display_address !== 'string') {
          throw Error('Address search returned an invalid candidate.');
        }
        if (candidate.identity_scope !== 'parcel_only'
            || typeof candidate.ambiguous_address !== 'boolean')
          throw Error('Invalid parcel candidate scope.');
        if (candidate.ambiguous_address && (!candidate.parcel_hint || typeof candidate.parcel_hint !== 'string'))
          throw Error('Ambiguous address lacks a parcel distinction.');
        const optionLabel = candidate.display_address
          + (candidate.ambiguous_address ? ' · ' + candidate.parcel_hint : '');
        const option = element('button', 'address-option', optionLabel);
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
                || resolved.identity_scope !== 'parcel_only'
                || resolved.building_identity_verified !== false
                || !/^\d{14}$/.test(resolved.pin)) {
              throw Error('The selected address did not resolve to a synthetic parcel.');
            }
            selectedAddressId = resolved.address_id;
            id('pin').value = resolved.pin;
            id('label').value = resolved.display_address.slice(0, 120);
            selectedAddress.hidden = false;
            const detail = candidate.ambiguous_address ? ' · ' + candidate.parcel_hint : '';
            text(selectedAddress, 'Selected: ' + resolved.display_address + detail
              + ' (fictional parcel only; building unverified)');
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

  // P6 fixture-only: a 2-3-property buyer workspace. Never infer a valuation
  // from comparable-sale data. Notes are mutable; evidence is never rewritten.
  let activeShortlist = null;
  const shortlistFeedback = id('shortlist-feedback');
  const shortlistEntries = id('shortlist-entries');
  const shortlistTable = id('shortlist-comparison');

  function shortlistMessage(message, ok = false) {
    shortlistFeedback.className = ok ? 'shortlist-feedback success' : 'shortlist-feedback';
    text(shortlistFeedback, message);
  }

  function rowValue(item, key) {
    const result = item.investigation;
    const subject = result.subject || {};
    if (key === 'price') return currencyAmount(subject.asking_price_usd) + ' (buyer-reported)';
    if (key === 'pin') return subject.pin ? 'Fictional PIN ' + subject.pin : 'Unresolved identity';
    if (key === 'area') return subject.building_area_sqft == null ? 'Not available' : String(subject.building_area_sqft) + ' sq ft (buyer-reported)';
    if (key === 'status') {
      const states = {
        supported_neighbourhood:'Same-neighbourhood evidence',
        exploratory_spatial:'Exploratory spatial fallback',
        insufficient_data:'Insufficient evidence',
        out_of_coverage:'Outside test coverage'
      };
      return states[result.status] || 'Unknown evidence status';
    }
    if (key === 'count') return String(result.selected_count ?? 0);
    if (key === 'tier') return result.tier === 'same_neighborhood' ? 'Neighbourhood' :
      result.tier === 'spatial_fallback' ? 'Exploratory 2 km' : 'No eligible evidence';
    if (key === 'date') return niceDate(result.analysis_date);
    if (key === 'snapshots') return (result.data_build?.source_snapshot_ids || []).join(', ') || 'Not available';
    if (key === 'rules') return item.match_policy_version || 'Unverified rule';
    if (key === 'warnings') return (result.warnings || []).join(' | ') || 'No additional warning';
    if (key === 'valuation') return 'Not produced';
    return 'Not available';
  }

  function renderShortlist(data) {
    if (data?.source_kind !== 'synthetic_fixture' || !uuid.test(data.shortlist_id)
        || data.max_entries !== 3 || !Array.isArray(data.entries) || data.entries.length > 3)
      throw Error('Invalid synthetic shortlist response.');
    for (const entry of data.entries) {
      if (!uuid.test(entry.investigation_id)
          || entry.investigation?.data_build?.source_kind !== 'synthetic_fixture'
          || entry.investigation.valuation !== null
          || entry.investigation.contract_version !== 'p3-draft-v0.3'
          || typeof entry.note_text !== 'string'
          || typeof entry.match_policy_version !== 'string')
        throw Error('Invalid saved investigation or note in shortlist response.');
    }
    activeShortlist = data.shortlist_id;
    id('shortlist-content').hidden = false;
    text(id('shortlist-title'), data.label);
    text(id('shortlist-count'), data.entries.length + ' / 3 properties selected. Choose two or three to compare.');
    text(id('shortlist-id-value'), 'Shortlist ID: ' + data.shortlist_id);
    id('shortlist-open-id').value = data.shortlist_id;
    id('shortlist-add-current').disabled = data.entries.length >= 3;
    history.replaceState(null, '', '#shortlist/' + data.shortlist_id);
    clear(shortlistEntries);

    if (!data.entries.length)
      shortlistEntries.appendChild(element('p', 'shortlist-empty', 'No properties selected. Investigate a fictional property above, then add its saved result.'));

    for (const [index, entry] of data.entries.entries()) {
      const investigation = entry.investigation;
      const label = investigation.subject?.label || 'Fictional property ' + (index + 1);
      const card = element('article', 'shortlist-entry');
      const header = element('div', 'shortlist-entry-head');
      const title = element('h4', '', label);
      header.appendChild(title);
      header.appendChild(element('span', 'shortlist-state', rowValue(entry, 'status')));
      card.appendChild(header);
      card.appendChild(element('p', 'shortlist-entry-meta',
        rowValue(entry, 'price') + ' · ' + (investigation.selected_count ?? 0) + ' selected sales'));
      const labelNode = element('label', '', 'Decision notes for ' + label);
      const note = element('textarea', 'shortlist-note');
      note.id = 'note-' + entry.investigation_id;
      note.maxLength = 800;
      note.rows = 3;
      note.value = entry.note_text;
      labelNode.htmlFor = note.id;
      card.appendChild(labelNode);
      card.appendChild(note);
      const actions = element('div', 'shortlist-entry-actions');
      const saveButton = element('button', 'secondary-button', 'Save notes');
      saveButton.type = 'button';
      saveButton.addEventListener('click', async () => {
        try {
          saveButton.disabled = true;
          const result = await requestJson('/v1/shortlists/' + activeShortlist + '/entries/' + entry.investigation_id,
            {method:'PATCH', headers:{'Content-Type':'application/json'},
              body:JSON.stringify({note_text:note.value})});
          renderShortlist(result);
          shortlistMessage('Notes saved without changing the original sale evidence.', true);
        } catch (error) { shortlistMessage('Could not save notes: ' + error.message); }
        finally { saveButton.disabled = false; }
      });
      const inspectButton = element('button', 'secondary-button', 'Inspect evidence');
      inspectButton.type = 'button';
      inspectButton.addEventListener('click', () => reopen(entry.investigation_id));
      const removeButton = element('button', 'secondary-button shortlist-remove', 'Remove');
      removeButton.type = 'button';
      removeButton.addEventListener('click', async () => {
        try {
          removeButton.disabled = true;
          const result = await requestJson('/v1/shortlists/' + activeShortlist + '/entries/' + entry.investigation_id,
            {method:'DELETE'});
          renderShortlist(result);
          shortlistMessage('Property removed from the shortlist; its original investigation remains saved.', true);
        } catch (error) { shortlistMessage('Could not remove property: ' + error.message); }
        finally { removeButton.disabled = false; }
      });
      actions.appendChild(saveButton);
      actions.appendChild(inspectButton);
      actions.appendChild(removeButton);
      card.appendChild(actions);
      shortlistEntries.appendChild(card);
    }

    const comparePanel = id('shortlist-compare');
    comparePanel.hidden = data.entries.length < 2;
    clear(shortlistTable);
    if (data.entries.length >= 2) {
      const head = document.createElement('thead');
      const tr = document.createElement('tr');
      tr.appendChild(element('th', '', 'Evidence field'));
      for (const [i, entry] of data.entries.entries())
        tr.appendChild(element('th', '', entry.investigation.subject?.label || 'Property ' + (i + 1)));
      head.appendChild(tr);
      shortlistTable.appendChild(head);
      const body = document.createElement('tbody');
      const fields = [
        ['Asking price', 'price'], ['Parcel identity', 'pin'],
        ['Building area', 'area'], ['Evidence support', 'status'],
        ['Eligible earlier sales', 'count'], ['Matching method', 'tier'],
        ['Analysis date', 'date'], ['Source snapshots', 'snapshots'],
        ['Matching rules', 'rules'], ['Evidence warnings', 'warnings'],
        ['Estimated current price', 'valuation']
      ];
      for (const [label, key] of fields) {
        const row = document.createElement('tr');
        const th = element('th', '', label);
        th.scope = 'row';
        row.appendChild(th);
        for (const entry of data.entries) row.appendChild(element('td', '', rowValue(entry, key)));
        body.appendChild(row);
      }
      shortlistTable.appendChild(body);
    }
  }

  async function loadShortlist(sid) {
    if (!uuid.test(sid)) { shortlistMessage('Use a valid lowercase shortlist UUID.'); return; }
    try {
      const data = await requestJson('/v1/shortlists/' + sid);
      renderShortlist(data);
      shortlistMessage('Saved fictional shortlist and frozen evidence reopened.', true);
    } catch (error) { shortlistMessage('Could not open shortlist: ' + error.message); }
  }

  id('shortlist-create-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const created = await requestJson('/v1/shortlists', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({label:id('shortlist-label').value.trim()})
      });
      renderShortlist(created);
      shortlistMessage('Fictional shortlist created. Add the current investigation.', true);
    } catch (error) { shortlistMessage('Could not create shortlist: ' + error.message); }
  });

  id('shortlist-open-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    await loadShortlist(id('shortlist-open-id').value.trim());
  });

  id('shortlist-add-current').addEventListener('click', async () => {
    if (!activeShortlist || !lastInvestigation) {
      shortlistMessage('First create or open a shortlist and investigate a property.'); return;
    }
    try {
      const result = await requestJson('/v1/shortlists/' + activeShortlist + '/entries', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({investigation_id:lastInvestigation})
      });
      renderShortlist(result);
      shortlistMessage('Saved property added without changing the recorded evidence.', true);
    } catch (error) { shortlistMessage('Could not add investigation: ' + error.message); }
  });

  id('shortlist-find').addEventListener('click', async () => {
    const found = id('shortlist-found');
    clear(found);
    try {
      const result = await requestJson('/v1/shortlists');
      if (result?.source_kind !== 'synthetic_fixture' || !Array.isArray(result.shortlists))
        throw Error('Invalid local shortlist index.');
      if (!result.shortlists.length) found.appendChild(element('p', '', 'No saved fictional shortlists in this database.'));
      for (const item of result.shortlists) {
        if (!uuid.test(item.shortlist_id)) throw Error('Invalid shortlist identifier.');
        const openButton = element('button', 'secondary-button', item.label + ' · ' + item.entry_count + ' homes');
        openButton.type = 'button';
        openButton.addEventListener('click', () => loadShortlist(item.shortlist_id));
        found.appendChild(openButton);
      }
      shortlistMessage('Local shortlists loaded. They are not private accounts.', true);
    } catch (error) { shortlistMessage('Could not list shortlists: ' + error.message); }
  });

  const startingShortlist = window.location.hash.match(/^#shortlist\/([0-9a-f-]+)$/);
  const starting = window.location.hash.match(/^#investigation\/([0-9a-f-]+)$/);
  if (startingShortlist) loadShortlist(startingShortlist[1]);
  else if (starting) reopen(starting[1]);
})();
