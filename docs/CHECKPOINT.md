# Current project checkpoint

**As of 22 November 2026**

**GitHub publication:** The standalone project repository is now at https://github.com/Sonkhe-Shongwe/house-price-intelligence on `main`. The initial 21 files were verified against the migration package; the seven offline tests also pass locally. The repository is currently **public**. See [GitHub setup](GITHUB_SETUP.md) for correct clone instructions. The live API extraction remains unverified.

**Objective:** Build House Price Intelligence as a functioning product, not just a machine-learning notebook. Preserve the pinnacle but prove the data and one bounded buyer journey first.

**Migrated:** Project brief and pinnacle framing, dataset feasibility research and source register, phase 0 Python audit, seven unit tests, run instructions, audit checkpoint and implementation decision history. Original docs in the private SA Tech Graduate Playbook have not been deleted or modified.

**Verified locally:** Existing audit tests pass on fabricated records. **Not verified:** network download of live Cook County datasets, actual counts and coverage, publishing rights of each field, trained models, final app backend/frontend/database, deployment.

**Immediate next step:** From `audit/phase0`, run the offline tests, then `python audit.py --township 17 --start 2022-01-01 --end 2025-01-01 --out output` on a computer that can reach the Cook County API. Inspect and return the generated report/errors. Do not commit `output/`.

**Decision gate:** The next substantive project decision depends on measured joins, real-data exclusions, geographical coverage, data terms and representative comparable examples.
