-- Shared empty-buyer ownership candidate; no accounts are seeded by DDL.
-- Fixture callers seed their own invented identities explicitly.
-- Empty buyer tables only; no silent assignment of an existing buyer's records.
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM investigations) OR EXISTS (SELECT 1 FROM shortlists) THEN
    RAISE EXCEPTION 'Explicit ownership migration required';
  END IF;
END $$;
CREATE TABLE workspace_owners (owner_id TEXT PRIMARY KEY);
ALTER TABLE investigations ADD COLUMN owner_id TEXT NOT NULL DEFAULT nullif(current_setting('hpi.owner_id',true),'') REFERENCES workspace_owners;
ALTER TABLE shortlists ADD COLUMN owner_id TEXT NOT NULL DEFAULT nullif(current_setting('hpi.owner_id',true),'') REFERENCES workspace_owners;
ALTER TABLE investigations ADD UNIQUE (investigation_id,owner_id);
ALTER TABLE shortlists ADD UNIQUE (shortlist_id,owner_id);
ALTER TABLE shortlist_investigations ADD COLUMN owner_id TEXT NOT NULL DEFAULT nullif(current_setting('hpi.owner_id',true),'');
ALTER TABLE shortlist_investigations ADD FOREIGN KEY (investigation_id,owner_id) REFERENCES investigations(investigation_id,owner_id);
ALTER TABLE shortlist_investigations ADD FOREIGN KEY (shortlist_id,owner_id) REFERENCES shortlists(shortlist_id,owner_id);
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE shortlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE shortlist_investigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE comparable_evidence ENABLE ROW LEVEL SECURITY;
CREATE POLICY own_investigations ON investigations USING (owner_id = nullif(current_setting('hpi.owner_id',true),''));
CREATE POLICY own_shortlists ON shortlists USING (owner_id = nullif(current_setting('hpi.owner_id',true),''));
CREATE POLICY own_members ON shortlist_investigations USING (owner_id = nullif(current_setting('hpi.owner_id',true),''));
CREATE POLICY own_results ON investigation_results USING (EXISTS (SELECT 1 FROM investigations i WHERE i.investigation_id=investigation_results.investigation_id));
CREATE POLICY own_evidence ON comparable_evidence USING (EXISTS (SELECT 1 FROM investigations i WHERE i.investigation_id=comparable_evidence.investigation_id));
