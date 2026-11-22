# Migration manifest and provenance

**Migration prepared:** 22 November 2026. **Source repository:** `Sonkhe-Shongwe/sa-tech-grad-playbook.` (note the literal trailing period in its repository name). Source default branch `main`.

| Source | Destination | Treatment |
| --- | --- | --- |
| `docs/portfolio/house-price-intelligence.md` | `docs/product/PRODUCT_BRIEF.md` | Faithful standalone adaptation; core rules and acceptance criteria carried forward |
| Expanded pinnacle vision developed in conversation | `docs/product/PINNACLE_VISION.md` | Explicitly marked future vision, not committed build scope |
| `docs/portfolio/house-price-data-feasibility.md` | `docs/research/DATA_FEASIBILITY.md` | Adapted: sources, core risks, tests, decisions, unknowns |
| Official source URLs from feasibility file | `docs/research/SOURCE_REGISTER.md` | Reorganized source/provenance table |
| `HousePriceIntelligence_Phase0_Audit/audit.py` | `audit/phase0/audit.py` | Copied unchanged from user-visible Phase 0 package |
| `HousePriceIntelligence_Phase0_Audit/tests/test_audit.py` | `audit/phase0/tests/test_audit.py` | Copied unchanged; seven unit tests |
| `HousePriceIntelligence_Phase0_Audit/README.md` | `audit/phase0/README.md` | Copied unchanged |
| `HousePriceIntelligence_Phase0_Audit/PROJECT_CHECKPOINT.md` | `audit/phase0/PROJECT_CHECKPOINT.md` | Original checkpoint copied unchanged |
| Current session decisions and outstanding concerns | `docs/DECISIONS.md`, `docs/CHECKPOINT.md`, `docs/ROADMAP.md`, `docs/engineering/ENGINEERING_CONTRACT.md` | New project-specific operating documentation |

No unrelated graduate vacancy research, other software portfolio projects, CVs, personal data or source dataset dumps were migrated. The two primary research documents were **adapted rather than byte-for-byte duplicated**; originals remain available in the playbook. No source repository paths were deleted or overwritten.

**Repository note:** The active GitHub connector can read and update existing repositories but has no remote repository-creation action. This initial project workspace must be pushed after an empty destination repository is created in GitHub.
