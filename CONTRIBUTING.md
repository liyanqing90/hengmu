# Contributing

Thank you for improving Hengmu.

## Before opening a change

Use an issue for a new workflow, schema-breaking change, or policy behavior
change. Small documentation, test, and correctness improvements may go directly
to a pull request.

Keep each change tied to one observable outcome. Separate:

- Skill activation or instruction changes;
- artifact schema or CLI contract changes;
- policy and quality-gate changes;
- repository-only documentation or automation.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --require-hashes -r requirements-dev.lock
```

Windows PowerShell users can activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## Local feedback loop

Keep the current worktree and select tests from the changed behavior, its callers,
and an adjacent failure path. Run those tests during development; the complete
checks below remain the pull request and release contract.

| Changed owner | Start with |
|---|---|
| Knowledge parsing, selection, or caches | `tests/test_target_architecture.py`, `tests/test_review_execution.py`, and the `selection_v14` cases in `tests/test_architecture_tool.py` |
| Repository or site validation | `tests/test_repository_contract.py`, `tests/test_site_contract.py` |
| Changed-line coverage | `tests/test_changed_coverage.py` |
| Packaging and release | `tests/test_package_plugin.py`, `tests/test_supply_chain.py`, `tests/test_release_publication.py` |

For example, after changing the coverage checker:

```bash
python3 -m pytest tests/test_changed_coverage.py -q --maxfail=1 --durations=5
python3 -m ruff check scripts/check_changed_coverage.py tests/test_changed_coverage.py
python3 -m ruff format --check scripts/check_changed_coverage.py tests/test_changed_coverage.py
```

Use explicit test node IDs to isolate a failure. After fixing it, rerun the
selected affected file groups so a passing isolated case does not hide an
adjacent regression. `--durations=5` identifies expensive cases without adding
a timing threshold to functional tests.

To check coverage before committing, generate fresh XML from the affected tests:

```bash
python3 -m pytest tests/test_changed_coverage.py --cov --cov-branch --cov-report=xml
python3 scripts/check_changed_coverage.py --local
```

`--local` compares against `HEAD` and includes staged, unstaged, and untracked
Python source under `scripts/` and `resources/scripts/`. Supply `--base-sha`
with a full commit hash to include earlier branch changes too. `--base-sha`
without `--local` checks committed changes only and also works outside CI.
Missing coverage records and uncovered new files fail the check. Regenerate XML
after edits; the checker does not certify that an existing report is fresh.

Passing local tests does not renew governance evidence. Changes to Selector
implementation inputs invalidate the old current-runtime lock. Keep historical
artifacts intact and produce new per-run Selection, Review, and verification
records before the change gate; preserve their source commits as described
below. Do not disable trust checks or reuse a historical verified status to
make a development result look release-ready.

## Making a Skill change

Every Skill must:

1. own one recognizable user goal;
2. keep only `name` and `description` in YAML frontmatter;
3. state trigger conditions and boundaries in the description;
4. use imperative instructions with explicit inputs and outputs;
5. point directly to every supporting reference it requires;
6. stay below 500 lines;
7. avoid repository README, changelog, or setup documents inside the Skill;
8. include deterministic scripts only when instructions alone are unreliable;
9. preserve rejected hypotheses and evidence limitations;
10. update direct, indirect, incomplete, negative, and edge cases in
    `evals/cases.yaml`.

When adding a Skill, generate `agents/openai.yaml` with the Codex
`skill-creator` helper and ensure `default_prompt` explicitly mentions the
Skill as `$skill-name`.

When changing packaging or host compatibility, update the compatibility matrix,
both public README languages, and the archive tests. Distinguish the portable
Agent Plugins format from a host-specific installation claim; only describe a
client as verified when a reproducible client/version result is recorded.

## Changing schemas or the CLI

- Treat artifact schemas and CLI exit codes as public contracts.
- Keep schema `1.0` readable and prefer additive, backward-compatible changes.
- Keep trusted schema `1.1` readable and use schema `1.2` for new
  facts/selection-bound artifacts.
- Update templates, tests, documentation, and changelog in the same pull
  request.
- Add a migration note before intentionally rejecting a previously valid
  artifact.
- Never weaken provenance, complete Rule Pack coverage, verification level,
  fingerprint, baseline, waiver, or risk-acceptance integrity to obtain a
  passing gate.
- Update the accepted decision record when a change alters authority,
  fingerprint semantics, public contracts, or trust boundaries.

## Changing architecture knowledge

- Define which decision an entry changes.
- Use standards, official documentation, or maintainer documentation.
- Follow `docs/knowledge-authoring.md` and record every required frontmatter
  field and body section.
- Keep architecture styles separate from technologies and current versions.
- Update Rule Packs only when a rule protects an invariant with testable
  evidence.
- Add or update an adversarial fixture when a change affects diagnosis,
  false-positive resistance, solution proportionality, or evidence quality.

## Maintaining bilingual documentation

`README.md` and `README.zh-CN.md` are one public contract in two languages.
When a user-visible capability, command, compatibility boundary, policy, or
project claim changes, update both files in the same pull request.

README visuals follow the same rule:

- English assets live in `docs/assets/brand/en/`,
  `assets/hengmu-readme-illustrations/en/`, and `diagrams/en/`;
- Simplified Chinese assets live in the corresponding `zh-CN/` directories;
- diagrams must include Mermaid, editable Excalidraw, rendered SVG, and PNG;
- localized pairs must preserve the same meaning, structure, and semantic
  colors, with only language-specific copy changing.

The SVG and Mermaid files are sources of truth. Regenerate their PNG,
SVG-derived, and Excalidraw outputs instead of editing rendered files alone.

## Required checks

Run:

```bash
python3 scripts/validate_repository.py
python3 resources/scripts/architecture_tool.py validate-project .
python3 resources/scripts/architecture_tool.py validate-history-anchors .
python3 resources/scripts/validate_knowledge.py
python3 -m pytest
python3 resources/scripts/architecture_tool.py gate --project . --stage change
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m pip_audit -r requirements-runtime.lock
python3 scripts/audit_licenses.py
python3 scripts/package_plugin.py --format codex --output-dir dist
python3 scripts/package_plugin.py --format agent-plugins --output-dir dist
python3 scripts/verify_checksum.py dist/*.zip.sha256
python3 scripts/generate_sbom.py \
  --archive dist/*.zip \
  --output-dir dist
```

The pull request should explain what each new test proves. A generated archive
is local evidence and should not be committed.

When a review or Selector Runtime binds source commits, preserve those commits
with a Merge Commit. Squash/rebase merging invalidates the source ancestry and
is rejected by `validate-history-anchors`.

## Pull request expectations

Include:

- the user-visible outcome;
- the affected Skill, schema, or policy boundary;
- compatibility implications;
- exact commands and observed results;
- activation cases added or changed;
- remaining limitations.

Do not include secrets, personal data, proprietary review artifacts, generated
caches, or unrelated formatting.

By contributing, you agree that your contribution is licensed under this
project's MIT License.
