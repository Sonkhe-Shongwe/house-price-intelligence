/** Isolated fictional P6 buyer workspace: source-owned shortlist state, never local notes. */
import { useEffect, useRef, useState } from 'react';
import {
  adaptInvestigation, adaptShortlist, adaptShortlistIndex, type ShortlistSummary,
  type InvestigationView, type ShortlistView,
} from './evidenceBridge';
import './savedComparison.css';
import ComparisonMatrix from './ComparisonMatrix';
import {evidenceLabel} from './HistoryPanel';
import {fixtureFetch} from './fixtureFetch';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

type WorkspaceProps = { active: InvestigationView | null };

async function api(path: string, method: 'GET' | 'POST' | 'PATCH' | 'DELETE', body?: object): Promise<unknown> {
  if (!path.startsWith('/v1/') || path.includes('//')) throw Error('invalid_source_route');
  const response = await fixtureFetch(path, {
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
function evidenceWasPreserved(previous: ShortlistView | null, next: ShortlistView, removedId?:string, allowMembershipChange=false) {
  if (!previous || previous.shortlistId !== next.shortlistId) return;
  for (const earlier of previous.entries) {
    if (earlier.investigationId===removedId) continue;
    const current = next.entries.find(entry => entry.investigationId === earlier.investigationId);
    if(!current&&allowMembershipChange)continue;
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
  const [recent,setRecent]=useState<ShortlistSummary[]>([]);
  const [recentError,setRecentError]=useState('');
  const recentSequence=useRef(0);
  const [label, setLabel] = useState('Fictional property research');
  const [reopenId, setReopenId] = useState('');
  const [otherId, setOtherId] = useState('');
  const [workspace, setWorkspace] = useState<ShortlistView | null>(null);
  const [notes, setNotes] = useState<Record<string,string>>({});
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [recoveryRequired,setRecoveryRequired]=useState(false);
  const locked = useRef(false);
  const live = useRef(true);

  async function loadRecent() {
    const sequence=++recentSequence.current;
    try {
      const rows=adaptShortlistIndex(await api('/v1/shortlists','GET'));
      if(live.current&&sequence===recentSequence.current){setRecent(rows);setRecentError('');}
    } catch(e) {
      if(live.current&&sequence===recentSequence.current){setRecent([]);setRecentError(previewError(e));}
    }
  }
  useEffect(()=>{
    live.current=true;
    void loadRecent();
    return ()=>{live.current=false;recentSequence.current++;};
  },[]);

  function hasDrafts() {
    return workspace?.entries.some(e=>notes[e.investigationId]!==e.noteText)??false;
  }
  const dirty=hasDrafts();
  useEffect(()=>{
    if(!dirty&&!busy&&!recoveryRequired)return;
    const warn=(event:BeforeUnloadEvent)=>{event.preventDefault();event.returnValue='';};
    window.addEventListener('beforeunload',warn);
    return ()=>window.removeEventListener('beforeunload',warn);
  },[dirty,busy,recoveryRequired]);

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
    removedId?: string,
  ) {
    if (locked.current||recoveryRequired) return;
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
      evidenceWasPreserved(workspace,reopened,removedId);
      install(reopened,true,savedNoteId);
      if (live.current) {setStatus(success);void loadRecent();}
    } catch (e) {
      if (live.current) {
        if(workspace)setRecoveryRequired(true);
        void loadRecent();
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
    if(hasDrafts()){setError('Save pending notes before creating another shortlist.');return;}
    const trimmed=label.trim();
    if (!trimmed || trimmed.length>80) {setError('Use a shortlist name between 1 and 80 characters.');return;}
    await perform(
      async () => adaptShortlist(await api('/v1/shortlists','POST',{label:trimmed})),
      result => {if (result.entries.length!==0) throw Error('new_shortlist_not_empty');},
      'Saved an empty fictional shortlist in the Python fixture database.',
    );
  }

  async function refresh(event?:React.FormEvent<HTMLFormElement>, chosenId?:string) {
    event?.preventDefault();
    const targetId=chosenId??reopenId.trim();
    const sameWorkspace=workspace?.shortlistId===targetId;
    if(!sameWorkspace&&(hasDrafts()||recoveryRequired)){
      setError('Refresh the current shortlist and resolve pending notes before switching.');return;
    }
    if (!UUID.test(targetId)) {setError('Enter a valid lowercase shortlist UUID.');return;}
    if (locked.current) return;
    locked.current=true;setBusy(true);setError('');setStatus('');
    try {
      const loaded=adaptShortlist(await api('/v1/shortlists/'+targetId,'GET'));
      if (loaded.shortlistId!==targetId)throw Error('shortlist_identity_conflict');
      evidenceWasPreserved(workspace,loaded,undefined,true);
      if(sameWorkspace&&workspace?.entries.some(e=>notes[e.investigationId]!==e.noteText&&
        !loaded.entries.some(next=>next.investigationId===e.investigationId))){
        throw Error('A property with an unsaved note is no longer on the shortlist. Copy your draft before leaving this page.');
      }
      install(loaded,sameWorkspace);
      if(live.current){setRecoveryRequired(false);setStatus('Shortlist reopened from Python, including stored notes.');void loadRecent();}
    } catch(e) {
      if(live.current){
        if(workspace&&sameWorkspace){setRecoveryRequired(true);}
        else {setWorkspace(null);setNotes({});setRecoveryRequired(false);}
        setError(previewError(e));
      }
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

  async function removeMember(investigationId:string) {
    if(!workspace||locked.current)return;
    const member=workspace.entries.find(e=>e.investigationId===investigationId);
    if(!member)return;
    if(notes[investigationId]!==member.noteText){
      setError('Save the note before removing this property.');return;
    }
    if(!window.confirm('Remove this property from the shortlist? Its saved investigation is retained.'))return;
    await perform(
      async()=>adaptShortlist(await api('/v1/shortlists/'+workspace.shortlistId+'/entries/'+investigationId,'DELETE')),
      result=>{
        const expected=workspace.entries.filter(e=>e.investigationId!==investigationId);
        if(result.shortlistId!==workspace.shortlistId||JSON.stringify(result.entries)!==JSON.stringify(expected))
          throw Error('removal_not_confirmed');
      },
      'Property removed from shortlist. Original investigation retained.',
      undefined,investigationId,
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
    {<form className="workspace-new-form" onSubmit={e=>void create(e)}>
      <label htmlFor="workspace-label">Name your research shortlist</label>
      <div className="workspace-input-line"><input id="workspace-label" data-testid="workspace-label"
        maxLength={80} value={label} onChange={e=>setLabel(e.target.value)}
        disabled={busy} required/>
        <button type="submit" data-testid="workspace-create" disabled={busy||recoveryRequired}>Create shortlist</button></div>
    </form>}
    <section aria-label="Recent saved shortlists">
      <h3>Saved shortlists</h3>
      <button type="button" disabled={busy} onClick={()=>void loadRecent()}>Refresh saved shortlists</button>
      {recentError&&<p role="alert">{recentError}</p>}
      {!recent.length&&!recentError&&<p>No saved shortlists yet.</p>}
      <ul data-testid="workspace-recent">{recent.map(row=><li key={row.id}>
        <button type="button" data-testid="workspace-open-recent" disabled={busy}
          onClick={()=>void refresh(undefined,row.id)}>{row.label} ({row.count}/3)</button>
      </li>)}</ul>
    </section>
    <form className="workspace-reopen" onSubmit={e=>void refresh(e)}>
      <label htmlFor="workspace-reopen-id">Open or refresh a saved shortlist UUID</label>
      <div className="workspace-input-line"><input id="workspace-reopen-id"
        data-testid="workspace-reopen-id" value={reopenId}
        onChange={e=>setReopenId(e.target.value)} maxLength={36} disabled={busy}
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"/>
        <button type="submit" data-testid="workspace-reopen" disabled={busy}>Open saved shortlist</button></div>
    </form>
    {workspace && <>
      {recoveryRequired&&<p role="alert" data-testid="workspace-recovery" className="source-error">
        Current server state is unconfirmed. The cards below are last-confirmed records and local drafts.
        Refresh this shortlist before making another change.
        <button type="button" disabled={busy} data-testid="workspace-recover"
          onClick={()=>void refresh(undefined,workspace.shortlistId)}>Refresh current shortlist</button>
      </p>}
      <div className="workspace-summary"><div><small>Saved shortlist / Python fixture</small>
        <h3>{workspace.label}</h3><span data-testid="workspace-id">{workspace.shortlistId}</span></div>
        <div><strong data-testid="workspace-count">{workspace.entries.length} / 3</strong>
          <small>Different properties</small></div></div>
      <div className="workspace-add">
        <button type="button" data-testid="workspace-add-current" disabled={!hasActive||busy||recoveryRequired}
          onClick={()=>active&&void addInvestigation(active.investigationId,active)}>
          Add current saved investigation
        </button>
        <form onSubmit={e=>{e.preventDefault();void addInvestigation(otherId);}}>
          <label htmlFor="workspace-other-id">Or add another saved investigation UUID</label>
          <div className="workspace-input-line"><input id="workspace-other-id"
            data-testid="workspace-other-id" value={otherId}
            onChange={e=>setOtherId(e.target.value)} maxLength={36}
            disabled={busy||recoveryRequired||workspace.entries.length>=3}/>
            <button type="submit" data-testid="workspace-add-id"
              disabled={busy||recoveryRequired||workspace.entries.length>=3}>Add saved ID</button></div>
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
            <p>{entry.investigation.subjectPin??'Unresolved parcel'} · {evidenceLabel(entry.investigation.status)}</p>
            <div className="workspace-money">{entry.investigation.askingPriceText}
              <small>Buyer-reported asking price, not a valuation</small></div>
            <label htmlFor={'workspace-note-'+index}>Buyer research note (stored separately)</label>
            <textarea id={'workspace-note-'+index} data-testid="workspace-note"
              rows={3} maxLength={800} value={note} disabled={busy}
              onChange={e=>setNotes(prev=>({...prev,[entry.investigationId]:e.target.value}))}/>
            <div className="workspace-card-bottom"><span data-testid="workspace-note-state">
              {recoveryRequired?'Awaiting server confirmation':dirty?'Unsaved changes':'Saved note verified'}</span>
              <button type="button" data-testid="workspace-save-note"
                disabled={!dirty||busy||recoveryRequired} onClick={()=>void saveNote(entry.investigationId)}>Save note</button>
            </div>
            <div className="workspace-provenance"><span>Frozen build · {entry.investigation.sourceBuildId}</span>
              <span>No verified map geometry</span></div>
            <button type="button" data-testid="workspace-remove" disabled={busy||dirty||recoveryRequired}
              onClick={()=>void removeMember(entry.investigationId)}>Remove property</button>
          </article>;
        })}
      </div>
      {!recoveryRequired&&workspace.entries.length>=2&&<section data-testid="workspace-comparison" className="pi-comparison">
        <h3>Evidence side by side</h3>
        <p>Compare the recorded facts, not an estimated selling price. Different source builds and analysis dates remain visible.</p>
        <ComparisonMatrix columns={workspace.entries.map(e=>({key:e.investigationId,title:e.investigation.subjectLabel}))}
          rows={([
            ['Asking price (buyer-reported)','money',e=>e.investigation.askingPriceText],
            ['Area',undefined,e=>e.investigation.buildingAreaText],
            ['Evidence quality','status',e=><span data-evidence={e.investigation.status}>{evidenceLabel(e.investigation.status)}</span>],
            ['Earlier sales','count',e=>String(e.investigation.selectedCount)],
            ['Analysis date',undefined,e=>e.investigation.analysisDate],
            ['Frozen build',undefined,e=>e.investigation.sourceBuildId],
            ['Snapshots',undefined,e=>e.investigation.sourceSnapshotIds.join(', ')],
            ['Matching rules',undefined,e=>e.matchPolicyVersion],
            ['Warnings',undefined,e=>e.investigation.warnings.join(' | ')||'None'],
            ['Valuation',undefined,()=> 'Not produced']
          ] as [string,'money'|'status'|'count'|undefined,(e:ShortlistView['entries'][number])=>import('react').ReactNode][]).map(([label,kind,value])=>({label,kind,values:workspace.entries.map(value)}))}/></section>}
    </>}
    {busy&&<p role="status" data-testid="workspace-busy">Confirming the change with the Python fixture service…</p>}
    {status&&<p role="status" data-testid="workspace-status" className="workspace-success">{status}</p>}
    {error&&<p role="alert" data-testid="workspace-error" className="source-error">{error}</p>}
    <p className="workspace-disclaimer">Stored notes belong to the selected local fictional database. SQLite persistence requires explicit fixture-file mode; PostgreSQL uses isolated fictional accounts. No production identity service, approved real property records, valuations or real geographic coordinates.</p>
  </section>;
}
