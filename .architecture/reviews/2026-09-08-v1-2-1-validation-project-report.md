# Hengmu 1.2.1 independent architecture verification

- Reviewed source: `0c8d633d1cc11892139ff61b83806f43a451e3c2`; source diff starts at `d6aadcb`.
- Scope: repository, with focused inspection of changed owners and adjacent contracts.
- Verification: V2, independent Codex agent `/root/release_verifier`, authorized identity `architecture-verifier`.
- Run: `hengmu-v1-2-1-independent-agent-verifier-20260908`; recorded at `2026-09-07T23:47:02.153638+00:00`.
- Candidate: `.architecture/reviews/2026-09-08-v1-2-1-validation-project-candidates.yaml`.
- Candidate SHA-256: `90729673847c6f1b355d7514970257ba3ab6badd04b7cd2ed038e4aa3c10c681`.
- Profile: `.architecture/reviews/inputs/2026-09-08-v1-2-1-validation-profile.yaml`.
- Canonical result: `.architecture/reviews/2026-09-08-v1-2-1-validation-project-verified.yaml`.

## Result and architecture

No supported defect was found in the candidate or in the independent inspection of the patch. Counts are raw 0, confirmed 0, rejected 0, needs-evidence 0; no separate strength Finding was created. This conclusion is bounded by the inspected evidence and does not establish release completion.

The unchanged architecture remains native/portable manifest → public router → focused Skill → shared schemas and deterministic local Python tooling. Audit candidates, independent verification, source and Knowledge bindings, and policy enforcement remain separate owners. The patch changes Knowledge parsing and similarity work, local coverage handling, unused internal declarations, and version identity.

The verifier inspected the changed source, its callers, removed-name consumers, relevant negative tests, all three Rule Packs, Profile, constraints, critical flows, fresh facts, twelve-entry Selection and compact Context. All selected entry hashes, candidate input hashes, Git source blobs and excerpt bounds were independently checked.

The strongest counter-hypotheses were that the faster loader could enable unsafe construction, the similarity bound could accept duplicates, local coverage could omit new files, deleted names could be public consumers, or wrapper removal could weaken candidate snapshot equality. Source and boundary tests contradict these explanations: both safe loaders reject Python object tags; only pairs below the upper bound skip unchanged exact comparison; missing and zero-hit new-file XML fail; deleted names have no repository consumers; and the same snapshot helper feeds the same mismatch rejection. A supplemental seeded local probe checked 20,000 token pairs with no changed threshold decision. This probe is not a configured Evidence Provider artifact or a quantified speed claim.

## Critical-flow and ownership assessment

| Flow | Assessment |
| --- | --- |
| Plugin discovery and Skill execution | Both 1.2.1 identities retain the same routing and local runtime contract. Installed-client acceptance is separate. |
| Finding verification and policy enforcement | Source candidate equality, role separation, schema authority and Provider provenance remain owned by their original boundaries. |
| Architecture knowledge and behavior evaluation | Safe parsing, root/schema/freshness checks, content-bound cache and exact 0.88 similarity decision remain authoritative. No model-quality inference is made. |
| Greenfield architecture decision | Approved Brief state, contained source context and exact source hash remain enforced. |
| Safe project initialization | Existing destinations are refused; staged state is validated before atomic directory publication. |
| Deterministic release packaging | Runtime allowlist, fixed archive metadata and exact inventory publication boundary remain in force; hosted publication is pending separate verification. |

All 31 Rule Pack rows occur exactly once: 28 assessed and three explicitly not applicable (frontend/backend business authority, multi-system transactions, distributed scheduling). All six critical flows are assessed. Three original candidate excerpts were too narrow to show the claimed checks; the verified YAML adds independently inspected snapshot-comparison, Brief-validation and publication bindings. Original candidate bytes were preserved.

## Deterministic evidence and checks

The clean Provider `test-results-20260907t232710827964z-0c8d633d1cc1` reports 372 tests, zero failures, errors or skips, and 118.756 seconds. The verifier independently matched the run and stdout/stderr/JUnit hashes and inspected clean start/end state. The older failed Provider records a missing `coverage` package in the former local environment and remains negative evidence only.

The following commands were run against this verified artifact and passed: `review-bindings` for the candidate; `validate-review`; `validate-coverage` (31 rules, six flows, twelve entries); and `verify-evidence` (empty error list). Signature verification is not required for this V2 zero-finding Review. No human V3, V4 or V5 identity is claimed.

## Limits

The passed Provider represents local macOS arm64 and its provisioned locked environment. Hosted OS/Python matrix, final release tag, immutable publication, asset attestations and installed-client behavior remain separate evidence. Neither stochastic model quality nor a numeric speed improvement is established here. Configured Provider execution is not an adversarial sandbox for arbitrary commands.

The reviewed source and passed Provider were clean. Fresh facts truthfully record `dirty: true` after untracked governance outputs appeared; creating this Review is not represented as a clean live working tree. Later source changes require reassessment under the declared scope and source-anchor policy.
