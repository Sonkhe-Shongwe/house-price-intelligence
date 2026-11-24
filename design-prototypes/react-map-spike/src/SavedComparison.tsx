/** Isolated fictional P6 buyer workspace: source-owned shortlist state, never local notes. */
import { useEffect, useRef, useState } from 'react';
import {
  adaptInvestigation, adaptShortlist,
  type InvestigationView, type ShortlistView,
} from './evidenceBridge';
import './savedComparison.css';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

type WorkspaceProps = { active: InvestigationView | null };

async function api(path: string, method: 'GET' | 'POST' | 'PATCH', body?: object): Promise<unknown> {
  if (!path.startsWith('/v1/') || path.includes('//')) throw Error('invalid_source_route');
  const response = await fetch(path, {
    method, credentials: 'same-origin', cache: 'no-store',
    ...(body === undefined ? {} : {
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    }),
  });
  const json: unknown = await response.json();
  if (!response.ok) {
    const data = json && typeof json === 'object' && !Array.isArray(json)
      ? json as Record<string, unknown> : {};
    const reason = typeof data.error === 'string' ? data.error : 'http_' + response.status;
    throw Error(reason);
  }
  return json;
}
function evidenceWasPreserved(previous: ShortlistView | null, next: ShortlistView) {
  if (!previous || previous.shortlistId !== next.shortlistId) return;
  for (const earlier of previous.entries) {
    const current = next.entries.find(entry => entry.investigationId === earlier.investigationId);
    if (!current || JSON.stringify(current.investigation) !== JSON.stringify(earlier.investigation)) {
      throw Error('frozen_evidence_changed');
    }
    if (current.matchPolicyVersion !== earlier.matchPolicyVersion) throw Error('match_policy_changed');
  }
}
function previewError(error: unknown): string {
  return error instanceof Error ? error.message : 'Source confirmation unavailable';
}

export default function SavedComparison({active}: WorkspaceProps) {
  const [enabled, setEnabled] = useState(false);
  const [checking, setChecking] = useState(true);
  const [availableError, setAvailableError] = useState('');
  const [label, setLabel] = useState('Fictional property research');
  const [reopenId, setReopenId] = useState('');
  const [otherId, setOtherId] = useState('');
  const [workspace, setWorkspace] = useState<ShortlistView | null>(null);
  const [notes, setNotes] = useState<Record<string,string>>({});
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const live = useRef(true);

  useEffect(() => {
    live.current = true;
    const controller = new AbortController();
    fetch('/_study/capabilities', {
      method:'GET',credentials:'same-origin',cache:'no-store',signal:controller.signal,
    }).then(async response => {
      if (!response.ok) throw Error('Fixture capability unavailable');
      const raw: unknown = await response.json();
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw Error('Invalid capability response');
      const data = raw as Record<string, unknown>;
      if (data.source_kind !== 'synthetic_fixture' ||
          typeof data.shortlist_writes !== 'boolean' ||
          typeof data.buyer_writes !== 'boolean') throw Error('Unexpected fixture capability');
      if (live.current) {
        setEnabled(data.shortlist_writes && data.buyer_writes);
        setChecking(false);
      }
    }).catch(e => {
      if (!controller.signal.aborted && live.current) {
        setAvailableError(previewError(e));setChecking(false);
      }
    });
    return () => {live.current = false;controller.abort();};
  }, []);

  if (checking) return <section className="workspace-shell" data-testid="workspace-checking" role="status">
    Checking fictional shortlist permissions…</section>;
  if (!enabled) return <section className="workspace-shell" data-testid="workspace-disabled">
    <div className="source-eyebrow">Next stage / separate permission</div>
    <h2>Saved comparison is read-only here.</h2>
    <p>This local preview has not enabled fictional shortlist writes. Restart with the explicit
      shortlist-workflow flag to create a workspace or save notes.</p>
    {availableError && <p role="alert">{availableError}</p>}
  </section>;

  function install(next:ShortlistView, preserveDrafts = false, savedNoteId?:string) {
    if (!live.current) return;
    // Confirmed writes update the server snapshot without silently discarding
    // unsaved edits on other cards. Explicit reopen resets local drafts.
    setNotes(previous => Object.fromEntries(next.entries.map(entry => {
      const before = workspace?.entries.find(e => e.investigationId === entry.investigationId);
      const draft = previous[entry.investigationId];
      const keepDraft = preserveDrafts && before && entry.investigationId !== savedNoteId &&
        typeof draft === 'string' && draft !== before.noteText;
      return [entry.investigationId, keepDraft ? draft : entry.noteText];
    })));
    setWorkspace(next);
    setReopenId(next.shortlistId);
  }

  async function perform(
    op: () => Promise<ShortlistView>,
    expected: (result:ShortlistView) => void,
    success: string,
    savedNoteId?: string,
  ) {
    if (locked.current) return;
    locked.current = true;setBusy(true);setError('');setStatus('');
    try {
      // A POST/PATCH may commit even if its response fails. Never auto-retry it.
      const serverResult = await op();
      expected(serverResult);
      const reopened = adaptShortlist(
        await api('/v1/shortlists/' + serverResult.shortlistId,'GET'));
      if (JSON.stringify(reopened) !== JSON.stringify(serverResult)) {
        throw Error('write_not_confirmed_by_frozen_get');
      }
      evidenceWasPreserved(workspace,reopened);
      install(reopened,true,savedNoteId);
      if (live.current) setStatus(success);
    } catch (e) {
      if (live.current) {
        setError(previewError(e) +
          '. Refresh the saved shortlist before repeating a write; a prior request may have committed.');
      }
    } finally {
      locked.current = false;
      if (live.current) setBusy(false);
    }
  }

  async function create(event:React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed=label.trim();
    if (!trimmed || trimmed.length>80) {setError('Use a shortlist name between 1 and 80 characters.');return;}
    await perform(
      async () => adaptShortlist(await api('/v1/shortlists','POST',{label:trimmed})),
      result => {if (result.entries.length!==0) throw Error('new_shortlist_not_empty');},
      'Saved an empty fictional shortlist in the Python fixture database.',
    );
  }

  async function refresh(event?:React.FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    if (!UUID.test(reopenId.trim())) {setError('Enter a valid lowercase shortlist UUID.');return;}
    if (locked.current) return;
    locked.current=true;setBusy(true);setError('');setStatus('');
    try {
      const loaded=adaptShortlist(await api('/v1/shortlists/'+reopenId.trim(),'GET'));
      if (loaded.shortlistId!==reopenId.trim())throw Error('shortlist_identity_conflict');
      evidenceWasPreserved(workspace,loaded);
      install(loaded);if(live.current)setStatus('Shortlist reopened from Python, including stored notes.');
    } catch(e) {
      if(live.current){setWorkspace(null);setNotes({});setError(previewError(e));}
    } finally {locked.current=false;if(live.current)setBusy(false);}
  }

  async function addInvestigation(investigationId:string, validated?:InvestigationView) {
    if (!workspace) {setError('Create or reopen a shortlist first.');return;}
    if (!UUID.test(investigationId)) {setError('Enter a valid saved investigation UUID.');return;}
    if (workspace.entries.length>=3) {setError('The backend accepts at most three properties.');return;}
    if (workspace.entries.some(entry => entry.investigationId===investigationId)) {
      setError('This investigation is already on the shortlist.');return;
    }
    await perform(async () => {
      const verified=adaptInvestigation(
        await api('/v1/investigations/'+investigationId,'GET'));
      if (verified.investigationId!==investigationId ||
          (validated && JSON.stringify(verified)!==JSON.stringify(validated))) {
        throw Error('investigation_changed_since_selection');
      }
      if (verified.subjectPin && workspace.entries.some(
        entry => entry.investigation.subjectPin===verified.subjectPin)) {
        throw Error('duplicate_property');
      }
      return adaptShortlist(await api(
        '/v1/shortlists/'+workspace.shortlistId+'/entries','POST',
        {investigation_id:investigationId,note_text:''}));
    }, result => {
      if (result.entries.length!==workspace.entries.length+1 ||
          !result.entries.some(e=>e.investigationId===investigationId)) {
        throw Error('member_not_confirmed');
      }
    },'Investigation added. Original saved sale evidence was preserved.');
  }

  async function saveNote(investigationId:string) {
    if(!workspace)return;
    const note = notes[investigationId];
    if (typeof note!=='string' || note.length>800 ||
        /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(note)) {
      setError('Notes must contain at most 800 characters without control characters.');return;
    }
    await perform(
      async()=>adaptShortlist(await api(
        '/v1/shortlists/'+workspace.shortlistId+'/entries/'+investigationId,
        'PATCH',{note_text:note})),
      result=>{
        if (result.entries.find(e=>e.investigationId===investigationId)?.noteText!==note) {
          throw Error('saved_note_not_confirmed');
        }
      },
      'Note saved in Python SQLite and verified by reopening the shortlist.',
      investigationId,
    );
  }

  const hasActive = active && workspace &&
    !workspace.entries.some(e=>e.investigationId===active.investigationId) &&
    !workspace.entries.some(e=>e.investigation.subjectPin &&
      e.investigation.subjectPin===active.subjectPin) && workspace.entries.length<3;

  return <section className="workspace-shell" data-testid="workspace">
    <div className="workspace-header">
      <div><div className="source-eyebrow">03 / Saved comparison</div>
        <h2>Build a shortlist.<br/><em>Keep evidence frozen.</em></h2>
        <p>Save up to three different fictional properties and annotate them through Python.
          Notes are editable; completed sales, provenance and matching rules are not.</p></div>
      <span className="workspace-flag">OPT-IN FIXTURE STORAGE</span>
    </div>
    {!workspace && <form className="workspace-new-form" onSubmit={e=>void create(e)}>
      <label htmlFor="workspace-label">Name your research shortlist</label>
      <div className="workspace-input-line"><input id="workspace-label" data-testid="workspace-label"
        maxLength={80} value={label} onChange={e=>setLabel(e.target.value)}
        disabled={busy} required/>
        <button type="submit" data-testid="workspace-create" disabled={busy}>Create shortlist</button></div>
    </form>}
    <form className="workspace-reopen" onSubmit={e=>void refresh(e)}>
      <label htmlFor="workspace-reopen-id">Open or refresh a saved shortlist UUID</label>
      <div className="workspace-input-line"><input id="workspace-reopen-id"
        data-testid="workspace-reopen-id" value={reopenId}
        onChange={e=>setReopenId(e.target.value)} maxLength={36} disabled={busy}
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"/>
        <button type="submit" data-testid="workspace-reopen" disabled={busy}>Open saved shortlist</button></div>
    </form>
    {workspace && <>
      <div className="workspace-summary"><div><small>Saved shortlist / Python fixture</small>
        <h3>{workspace.label}</h3><span data-testid="workspace-id">{workspace.shortlistId}</span></div>
        <div><strong data-testid="workspace-count">{workspace.entries.length} / 3</strong>
          <small>Different properties</small></div></div>
      <div className="workspace-add">
        <button type="button" data-testid="workspace-add-current" disabled={!hasActive||busy}
          onClick={()=>active&&void addInvestigation(active.investigationId,active)}>
          Add current saved investigation
        </button>
        <form onSubmit={e=>{e.preventDefault();void addInvestigation(otherId);}}>
          <label htmlFor="workspace-other-id">Or add another saved investigation UUID</label>
          <div className="workspace-input-line"><input id="workspace-other-id"
            data-testid="workspace-other-id" value={otherId}
            onChange={e=>setOtherId(e.target.value)} maxLength={36}
            disabled={busy||workspace.entries.length>=3}/>
            <button type="submit" data-testid="workspace-add-id"
              disabled={busy||workspace.entries.length>=3}>Add saved ID</button></div>
        </form>
      </div>
      {workspace.entries.length===0 && <p className="workspace-empty" data-testid="workspace-empty">
        Your shortlist is saved but contains no properties. Add the current investigation
        or an existing saved investigation ID.</p>}
      <div className="workspace-grid" data-testid="workspace-entries">
        {workspace.entries.map((entry,index)=>{
          const note=notes[entry.investigationId]??'';
          const dirty=note!==entry.noteText;
          return <article className="workspace-card" key={entry.investigationId}
            data-testid="workspace-entry">
            <div className="workspace-card-top"><span>PROPERTY {String(index+1).padStart(2,'0')}</span>
              <span className="workspace-evidence-badge">{entry.investigation.selectedCount} earlier sales</span></div>
            <h3>{entry.investigation.subjectLabel}</h3>
            <p>{entry.investigation.subjectPin??'Unresolved parcel'} · {entry.investigation.status}</p>
            <div className="workspace-money">{entry.investigation.askingPriceText}
              <small>Buyer-reported asking price, not a valuation</small></div>
            <label htmlFor={'workspace-note-'+index}>Buyer research note (stored separately)</label>
            <textarea id={'workspace-note-'+index} data-testid="workspace-note"
              rows={3} maxLength={800} value={note} disabled={busy}
              onChange={e=>setNotes(prev=>({...prev,[entry.investigationId]:e.target.value}))}/>
            <div className="workspace-card-bottom"><span data-testid="workspace-note-state">
              {dirty?'Unsaved changes':'Saved note verified'}</span>
              <button type="button" data-testid="workspace-save-note"
                disabled={!dirty||busy} onClick={()=>void saveNote(entry.investigationId)}>Save note</button>
            </div>
            <div className="workspace-provenance"><span>Frozen build · {entry.investigation.sourceBuildId}</span>
              <span>No verified map geometry</span></div>
          </article>;
        })}
      </div>
    </>}
    {busy&&<p role="status" data-testid="workspace-busy">Confirming the change with the Python fixture service…</p>}
    {status&&<p role="status" data-testid="workspace-status" className="workspace-success">{status}</p>}
    {error&&<p role="alert" data-testid="workspace-error" className="source-error">{error}</p>}
    <p className="workspace-disclaimer">Stored notes are only in this disposable local SQLite session.
      There are no accounts, private user data, source-publisher rights, real property valuations or geographic coordinates.</p>
  </section>;
}
