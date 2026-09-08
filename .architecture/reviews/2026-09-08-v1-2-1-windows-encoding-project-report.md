# Hengmu 1.2.1 Windows encoding verification

- Reviewed commit: `6d5d965106674e8c1e4c9e24cfeb49f2ef08e33c`; correction base: `ffde0b9`.
- Scope: repository and the complete 1.2.1 patch, with fresh inspection of the Windows Git decoding owner and consumers.
- Verification: V2, independent Codex agent `/root/release_verifier`, identity `architecture-verifier`.
- Run: `hengmu-v1-2-1-windows-encoding-independent-verifier-20260908`, recorded at `2026-09-08T02:56:59.943027+00:00`.
- Candidate: `.architecture/reviews/2026-09-08-v1-2-1-windows-encoding-project-candidates.yaml`.
- Candidate SHA-256: `20efd1d368affbe11e12d8018d7b5c6a606b90fa45b10a6eb963cbb068e676dc`.
- Profile: `.architecture/reviews/inputs/2026-09-08-v1-2-1-windows-encoding-profile.yaml`.
- Canonical result: `.architecture/reviews/2026-09-08-v1-2-1-windows-encoding-project-verified.yaml`.

## Result

No unresolved supported defect was found at the corrected source commit. Raw findings 0; confirmed 0; rejected 0; needs-evidence 0. No separate strength Finding was created. This fresh V2 result does not reuse the previous Review's verified status and does not establish hosted Windows or release completion.

The verifier independently retrieved [failed CI run 34180031724](https://github.com/qingye-lab/hengmu/actions/runs/34180031724). Windows 3.11 and 3.14 failed the Unicode changed-path case. The returned spelling is consistent with Git UTF-8 bytes decoded using cp1252. The verifier then used a separate temporary Git repository, the old helper, the current helper and a forced cp1252 default: the old helper produced the wrong names; the corrected helper preserved both committed and untracked Chinese paths.

The fix belongs in `scripts/check_changed_coverage.py::git`, shared by NUL-delimited diff/untracked enumeration and full-SHA lookups. Explicit UTF-8 decoding protects path identity before coverage XML comparison. It does not alter scope, baseline selection, required records, coverage thresholds or error policy. The real-Git regression exercises both path-producing commands while keeping its locale simulation scoped. The three-file correction consists only of that decoding choice, its regression and the changelog.

## Architecture, coverage and critical flows

The package remains manifest → public entry → focused Skill → shared schema and local deterministic runtime. Current hashes confirm the prior runtime source, schemas, Knowledge content, Rule Packs, provider owner and publication algorithm remain unchanged by the Windows correction. Their current evidence and candidate conclusions were reassessed together with the new owner and negative-path test, rather than treating an earlier verified state as new evidence.

All 31 loaded Rule Pack rules occur once: 28 assessed and three explicitly not applicable for absent frontend/backend business authority, multi-system transactions and distributed scheduling. All six critical flows are assessed:

| Flow | Current assessment |
| --- | --- |
| Plugin discovery and Skill execution | Native and portable identities retain nine public Skills and the focused routing boundary. |
| Finding verification and policy enforcement | Candidate snapshot equality, source/profile/rule hashes, role separation and Provider provenance remain enforced. |
| Architecture Knowledge and behavior evaluation | Safe-loader fallback, root/schema/freshness checks, copied content-bound cache and exact golden similarity remain authoritative. |
| Greenfield architecture decision | Contained, approved Brief identity and source hash remain required. |
| Safe project initialization | Existing targets are refused and staged valid state is atomically published. |
| Deterministic release packaging | Allowlist, fixed archive metadata, exact asset inventory and immutable-publication checks remain release owners. |

The verifier checked all 29 distinct original Git source bindings at the reviewed commit, fresh facts/Profile/Selection hashes and all thirteen selected entry hashes. One coverage-test excerpt ended before assertions shifted by the new test; the verified artifact adds the exact continuation without changing candidate bytes. Recommended Knowledge selection is context, not evidence that an unrelated architectural pattern applies.

## Evidence and limits

The fresh clean Provider `test-results-20260908t024801953604z-6d5d96510667` reports 373 tests, zero failures, errors or skips, and 82.228 seconds. Run and stdout/stderr/JUnit hashes were independently matched, and start/end commits and clean state were inspected. This local macOS arm64 run and the forced-cp1252 regression are distinct from a real hosted Windows pass. The former missing-coverage failure remains retained negative environment evidence.

Review bindings, Review validation, coverage validation (31 rules, six flows, thirteen entries) and evidence resolution (empty error list) all ran and passed for this new artifact. No SSH signature or human V3-V5 identity is claimed or required for this V2 zero-finding result. Fresh facts truthfully report `dirty: true` after governance outputs appeared; the recorded source and Provider execution were clean.

Refreshed Windows 3.11/3.14 jobs, final hosted quality gate, tag, exact remote inventory, asset attestations and immutable publication still require direct completion evidence. Earlier installed-package observations remain bounded to their recorded host. No stochastic model improvement, numeric speed guarantee, broader client support or adversarial sandbox for arbitrary Provider commands is established.
