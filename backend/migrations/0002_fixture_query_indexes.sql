-- P3 fixture-only upgrade. No real-source tables, address provider or migration.
-- Search uses instr() and is not accelerated by this index; these indexes
-- target real relational joins and retrieval paths already in the fixture.
CREATE INDEX idx_fixture_sale_link_parcel ON sale_transaction_parcels(pin, transaction_id);
CREATE INDEX idx_fixture_assessment_parcel_year ON assessment_records(pin, tax_year);
CREATE INDEX idx_fixture_investigation_build_date ON investigations(build_id, analysis_date);
