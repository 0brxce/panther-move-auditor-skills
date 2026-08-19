# Autonomous Workflow

Use this file for full `move-auditor` runs. It turns the existing Move pattern
library into an autonomous, artifact-backed audit loop.

## Operating Model

The auditor owns the whole run:

1. Ingest source, docs, optional operator context, and build/test state.
2. Map the complete Move attack surface into auditable scopes.
3. Route every scope through the applicable Move, Sui, Aptos, DeFi, semantic,
   and false-positive references.
4. Deep-audit scopes one at a time.
5. Compose cross-scope attack chains.
6. Verify, refute, or downgrade every candidate.
7. Produce a report only from evidence-backed findings.

Do not treat a command finishing, a model answer, or a lack of findings as audit
completion. Completion requires artifacts, coverage accounting, and a clear
finding status split.

## Run Directory

At the start of a full run, create or reuse `.move-auditor/` in the target
project root. If artifacts already exist, read them first and resume instead of
discarding prior coverage.

Required artifacts:

- `run.json`
- `coverage-plan.json`
- `scopes.json`
- `candidate-findings.json`
- `verification-results.json`
- `confirmed-findings.json`
- `dismissed-findings.json`
- `clean-checks.json`
- `resource-requests.json`
- `progress.json`
- `progress.md`
- `dashboard.html`
- `report.md`

Use `artifact-schema.md` for field definitions. Keep artifacts valid JSON except
for `progress.md`, `dashboard.html`, and `report.md`.

## Progress UI

A full autonomous run must expose live progress in two places:

1. the agent-facing plan/checklist for the current Codex or Claude session;
2. progress artifacts under `.move-auditor/` for the target project.

Create or refresh these files at run start, every phase transition, before and
after build/test commands, after each audited scope, whenever finding counts
change, whenever a blocker appears, and at completion:

- `progress.json` - machine-readable current run state
- `progress.md` - compact human-readable progress dashboard
- `dashboard.html` - self-contained browser-openable progress dashboard

`dashboard.html` must not depend on a server, external JavaScript, external CSS,
or remote assets. Regenerate it from the same state as `progress.json`, using
`scripts/render_progress.py` when available. Include current phase, active scope,
latest command, audited/pending/blocked scope counts, candidate/confirmed/
dismissed counts, blockers, latest events, and next action.

Do not say progress is shown in a UI unless `progress.md`, `dashboard.html`, or a
real control-plane URL exists. If only the chat plan is updated, call it a plan
update, not a UI. A phase gate is not complete until the progress artifacts
reflect the phase result.

## Optional Operator Context

Operator context is optional. The autonomous scan must still work without it.

Accept context from either:

- text supplied in the user's prompt under headings such as `Audit Context`,
  `Known Issues`, `Focus Areas`, `Threat Model`, or `Out of Scope`;
- `.move-auditor/context.md`;
- `audit-context.md`, `security-context.md`, `known-issues.md`, or files the
  user explicitly names.

Record all loaded context in `run.json.operator_context` with:

- `source`: prompt or file path
- `classification`: `scope`, `known_issue`, `threat_model`, `focus_area`,
  `out_of_scope`, `deployment`, `other`
- `summary`: short factual summary
- `answer_bearing`: true when it names a suspected bug, location, exploit, or
  mechanism

Use answer-bearing context as a lead for a targeted verification pass, not as
proof and not as evidence for blind-discovery claims. If the user requests a
blind audit, do not load known-issue material unless they explicitly override.

## Phase Gates

### Phase A - Intake

Outputs: `run.json`, initial `resource-requests.json`, initialized progress
artifacts

Required actions:

- Identify chain: Sui, Aptos, mixed, or unknown Move.
- Locate build root, `Move.toml`, source directories, tests, docs, and package
  metadata.
- Capture optional operator context.
- Initialize `progress.json`, `progress.md`, and `dashboard.html`.
- Try build detection:
  - Sui: `sui move build`
  - Aptos: `aptos move compile`
- If build tooling is missing or dependencies cannot resolve, record a resource
  request and continue static analysis.

Gate to continue: `run.json` exists with target summary, chain, source roots,
build status, and context summary.

### Phase B - Surface Map

Outputs: `scopes.json`

Load `scope-mapping.md`. Enumerate concrete audit scopes, not broad modules.
Every public/entry surface, value-flow gate, capability boundary, shared object,
fixed-point helper, oracle consumer, admin path, and cross-module invariant must
either be a scope or be covered by a scope.

Gate to continue: `scopes.json` exists with at least one scope for every detected
public attack surface, or `resource-requests.json` explains why mapping is
blocked.

### Phase C - Coverage Routing

Outputs: `coverage-plan.json`

Load `checklist-router.md` and all always-loaded references. Based on signals,
load chain-specific and protocol-specific references. Attach required check IDs
to each scope where possible.

Gate to continue: every fired route appears in `coverage-plan.json` with the
reference files loaded and mandatory follow-ups listed.

### Phase D - Scope Audit

Outputs: `candidate-findings.json`, `clean-checks.json`, updated `scopes.json`

Audit scopes in priority order. For each scope:

- Read the exact source region and all caller/callee paths needed to understand
  the invariant.
- Run assigned checks from the coverage plan.
- For each clean check, write a concise clean-check row with the evidence tag.
- For each candidate, write a candidate finding with exact location, attacker
  path, preconditions, impact, and evidence tags.
- Mark the scope `audited`, `blocked`, or `needs-followup`.

Do not write "safe" notes to candidate findings. Clean coverage belongs in
`clean-checks.json`.

### Phase E - Cross-Scope Synthesis

Outputs: additional candidate findings or clean checks

After individual scopes, trace composition bugs:

- entry point -> authorization -> value movement
- oracle check -> settlement transfer
- reward/checkpoint update -> every user/admin operation
- admin config -> runtime accounting
- Sui PTB multi-call sequence -> per-call limits
- package/version boundary -> live shared objects
- bridge/source-chain finality -> Move destination validation

For lending protocols, run these mandatory interaction pairs:

1. Reward/accumulator update vs all lending operations: if update arithmetic can
   abort before checkpointing and every deposit/withdraw/borrow/repay/liquidate/
   claim/admin recovery path calls it, check for permanent deadlock.
2. Repay vs rewards/liquidity mining: when the last debt is cleared, verify the
   reward tracker or obligation-linked accounting is cleaned up.
3. Liquidation vs collateral reserve: verify idle cash or available collateral is
   checked before `balance::split()` or equivalent seizure.
4. ADL vs emode/group state: entry and stop conditions must read debt and risk
   from the same source.
5. Admin config vs interest/reserve state: rate/fee/model changes must accrue or
   checkpoint before applying new parameters.
6. Liquidation vs close factor: Sui PTBs must not bypass per-call liquidation
   limits by repeatedly calling liquidation in one transaction.
7. Admin config vs rate limiters: config updates must preserve limiter segments,
   counters, accumulated usage, and rollover state.
8. Oracle eligibility vs oracle seize/settlement: trigger and settlement must use
   the same price basis or bounded divergence with no permanent retry DoS.
9. Flash loan vs deposit/borrow/withdraw: mid-PTB operations must not read stale
   cash, debt, or share accounting unless the hot-potato design proves safety.

### Phase F - Verification

Outputs: `verification-results.json`, `confirmed-findings.json`,
`dismissed-findings.json`

Load `verification-policy.md`, `evidence-chains.md`, `confidence-gates.md`,
and `verification-runner.md`.

Every candidate must end as one of:

- `confirmed`: reproducible by local command, math proof plus code evidence, or
  production read-only state plus code evidence.
- `likely`: strong source/math evidence, but no executable proof.
- `needs_review`: plausible but missing decisive proof.
- `dismissed`: disproven by trusted evidence.
- `overclassified`: real issue with downgraded impact.
- `blocked`: tooling, dependency, or missing artifact prevented verification.

High and Critical require a concrete attacker path, victim, broken invariant,
harmful postcondition, and either executable proof or hard evidence satisfying
`confidence-gates.md`.

### Phase G - Report

Outputs: `report.md`

Report only `confirmed`, `likely`, and explicitly retained `needs_review`
findings. Separate confirmed issues from needs-review issues. Include dismissed
findings and clean checks in appendices, not as vulnerabilities.

The report must include:

- scope and build status
- optional context used and whether it was answer-bearing
- coverage summary: total scopes, audited, blocked, pending
- severity summary
- finding table
- detailed findings with attacker path, evidence, verification, and fix
- verified clean checks
- blocked resources and residual risk

## Priority Model

Prioritize scopes in this order:

1. Direct value movement, mint/burn, withdraw, redeem, borrow, liquidate, claim.
2. Public unrestricted state mutation.
3. Shared objects and Sui `public fun` PTB-composable paths.
4. Oracle, price, index, checkpoint, fixed-point, and rate-model logic.
5. Capability, admin, upgrade, signer, and policy boundaries.
6. Bridge, message, signature, and cross-chain recipient semantics.
7. Cleanup, close, reclaim, migration, and emergency paths.
8. Integration surfaces and view/helper functions that feed user decisions.

## Non-Negotiable Rules

- Never report a finding without exact source location.
- Never promote a pattern match without a concrete exploit story.
- Never dismiss a candidate with mocks, comments, or docs alone.
- Never assume EVM behavior applies to Move.
- Never call a run complete while high-priority scopes are pending and no
  coverage/resource artifact explains why.
- Never mutate target source as part of the audit unless the user explicitly
  asks for fixes. Verification tests or scratch files are allowed.
