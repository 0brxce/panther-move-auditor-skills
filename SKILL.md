---
name: move-auditor
description: Autonomous security auditor for Move contracts (Sui & Aptos).
metadata:
  version: "4.0.0"
  author: pantheraudits
  category: security
  tags:
    - move
    - sui
    - aptos
    - smart-contract-audit
    - web3-security
---

# Move Auditor

> Autonomous, artifact-backed security auditing for Sui and Aptos Move.
> Activates on `.move` files and runs from scope mapping to verified report.

## Activation

Use this skill whenever:

- `.move` files are in the working directory or opened in the editor
- the user asks to audit, review, scan, or find vulnerabilities in Move code
- keywords such as `module`, `struct`, `entry fun`, `public fun`, `sui::`,
  `aptos_framework::`, `Move.toml`, `UID`, or `&signer` appear in scope

When activated for an audit, immediately start the autonomous workflow. Do not
wait for more instructions unless authorization or target scope is genuinely
unclear.

## Do Not Use

- Non-Move contracts or programs
- General style/performance/refactor review
- Fixing code unless the user explicitly asks for patches
- Quick scans when the user explicitly says not to run full verification

## Reference Files

All reference files live beside this `SKILL.md`.

| File | When to load |
| --- | --- |
| `autonomous-workflow.md` | Always for full audits; phase gates, run loop, optional context, artifacts |
| `artifact-schema.md` | Always for full audits; JSON artifact and progress UI formats |
| `scope-mapping.md` | Phase B; Move-specific scope inventory |
| `verification-runner.md` | Phase F; local proof, Sui/Aptos build-test, promotion rules |
| `common-move.md` | Always; chain-agnostic checks and build/test log analysis |
| `verification-policy.md` | Always and Phase F; evidence hierarchy and feasibility gates |
| `checklist-router.md` | Always; deterministic routing from signals to check files |
| `move-fp-catalog.md` | Always; false-positive catalog and hallucination checks |
| `sui-patterns.md` | Sui targets; SUI-01 to SUI-45 |
| `aptos-patterns.md` | Aptos targets; APT-01 to APT-25 |
| `defi-vectors.md` | Tokens, swaps, lending, staking, oracles, bridges; DEFI-01 to DEFI-10 |
| `semantic-gap-checks.md` | Accumulators, checkpoints, rewards, lending state, cross-module accounting |
| `defi/defi-staking.md` | Staking/yield; DEFI-11 to DEFI-16, DEFI-88 |
| `defi/defi-oracle.md` | When oracle usage is detected (`get_price`, `oracle`, `price_feed`, `price_info`, `oracle_update`, `refresh_oracle`, `observation`) — DEFI-17 to DEFI-24, DEFI-95 |
| `defi/defi-lending.md` | Lending/borrow/rate limits/margin; DEFI-25 to DEFI-34, DEFI-80, DEFI-82, DEFI-84, DEFI-90, DEFI-93 |
| `defi/defi-math-precision.md` | Fixed-point, precision, reward math, check-vs-settle; DEFI-35 to DEFI-42, DEFI-85 to DEFI-87, DEFI-92 |
| `defi/defi-slippage.md` | Swaps/DEX/slippage/MEV; DEFI-43 to DEFI-49 |
| `defi/defi-liquidation.md` | Liquidation/ADL/bad debt/insurance; DEFI-50 to DEFI-66, DEFI-81, DEFI-83, DEFI-91, DEFI-94 |
| `defi/defi-auction-clm.md` | Auctions and concentrated liquidity; DEFI-67 to DEFI-73 |
| `defi/defi-signatures.md` | Signatures, nonce, signer-set, quorum; DEFI-74 to DEFI-79, DEFI-89 |
| `defi/defi-lending-design-patterns.md` | Known-good lending patterns; load before reporting design-pattern bugs |
| `evidence-chains.md` | Phase F; data-flow, math, PoC, negative-PoC templates |
| `confidence-gates.md` | Phase F; hard evidence and confidence gating |
| `audit-prompts.md` | Optional deep-dive prompts |
| `sample-finding.md` | Output example only; do not load during normal audits |

## Autonomous Workflow

For full audits, read `autonomous-workflow.md`, `artifact-schema.md`,
`scope-mapping.md`, `common-move.md`, `verification-policy.md`,
`checklist-router.md`, and `move-fp-catalog.md` before acting.

For full autonomous runs, create and maintain `.move-auditor/progress.json`,
`.move-auditor/progress.md`, and `.move-auditor/dashboard.html`. Keep them
synchronized with phase gates, scope progress, command results, blockers, and
finding counts. After updating `progress.json`, use
`scripts/render_progress.py` when available; resolve it relative to this
`SKILL.md` and pass the target project's `.move-auditor/progress.json`.

Run these phases:

1. **Intake** - detect chain, build root, docs, optional operator context, build
   and test availability. Write `.move-auditor/run.json` and initialize progress
   UI artifacts.
2. **Surface Map** - enumerate every concrete audit scope using
   `scope-mapping.md`. Write `.move-auditor/scopes.json`.
3. **Coverage Router** - use `checklist-router.md` to load chain/protocol files
   and attach checks to scopes. Write `.move-auditor/coverage-plan.json`.
4. **Scope Audit** - audit scopes one at a time. Write candidates to
   `.move-auditor/candidate-findings.json` and clean checks to
   `.move-auditor/clean-checks.json`.
5. **Cross-Scope Synthesis** - compose bugs that span modules, operations, PTB
   steps, shared objects, package versions, or check/settlement paths.
6. **Verification** - load `evidence-chains.md`, `confidence-gates.md`, and
   `verification-runner.md`; confirm, downgrade, dismiss, or block every
   candidate. Write verification, confirmed, and dismissed artifacts.
7. **Report** - write `.move-auditor/report.md` from evidence-backed findings,
   with coverage, context, residual risk, and clean-check summaries.

If `.move-auditor/` already exists, read existing artifacts and resume. Do not
silently throw away prior coverage.

Do not claim progress is visible in a UI unless `progress.md`, `dashboard.html`,
or a real control-plane URL exists. If only the chat plan changed, describe it as
a plan update.

## Optional Audit Context

The user may provide optional context at the start, for example:

```text
Audit Context:
- Known issue: ...
- Focus area: ...
- Out of scope: ...
- Deployment/package IDs: ...
```

Also check for `.move-auditor/context.md`, `audit-context.md`,
`security-context.md`, and `known-issues.md` when present. Record loaded context
in `run.json.operator_context`. Treat known issues as leads for verification, not
as proof. If the user asks for a blind audit, skip answer-bearing known-issue
material unless they explicitly override.

## Chain And Scope Rules

- Sui detection: `sui::object`, `sui::transfer`, `sui::tx_context`, `UID`,
  `Clock`, shared objects, PTB-facing functions.
- Aptos detection: `aptos_framework`, `aptos_std`, `signer`, `account`,
  `coin`, `fungible_asset`, `timestamp`, `#[test_only]`.
- Sui `public fun` is PTB-callable and must be treated as attack surface.
- Aptos `public fun` is module-callable only unless it is also `entry`.
- Classify each entry point as public-unrestricted, capability-gated,
  owner-gated, signer-gated, package-gated, or review-required.
- Public-unrestricted state mutation is top priority.

## Mandatory High-Value Passes

Always run these when signals exist:

- Production-surface parity gate: enumerate source attributes, treat
  non-production labels as untrusted, review compiler warnings, and compare the
  emitted module API with the intended publish API. Audit every surviving helper
  by its real bytecode visibility and authorization (common-move.md 1.7).
- Fixed-point helper gate: identify helpers, read `mul`/`div`/`from`, derive
  bounds, inspect call sites, and check abort-before-checkpoint recoverability.
- Sui stale-package gate: every shared object needs versioning and every public
  surface taking that object must assert current version.
- Reward/checkpoint deadlock gate: reward, interest, or accumulator updates must
  not overflow before checkpointing when all user/admin paths call them.
- Check-vs-settlement trace: liquidation, swap, ADL, fill, redeem, or withdraw
  checks must use the same value basis as settlement or handle bounded divergence
  without permanent retry DoS.
- PTB multi-call pass: on Sui, per-call limits must survive repeated calls in one
  programmable transaction block.
- Same-transaction oracle snapshot pass: when a mutable observation update and
  correlated pricing/value-moving functions coexist, verify transaction
  provenance or an immutable snapshot prevents mixed observations (DEFI-95).
- Semantic-gap pass: stale/mismatched writer-consumer paths for accounting,
  rewards, lending, liquidation, oracle, and checkpoint state.
- Cross-module lending pass: reward manager, repay cleanup, liquidation cash,
  ADL/emode source, pre-accrual admin config, close factor, limiter state,
  oracle trigger/seize basis, and flash-loan mid-PTB accounting.

## Verification Standards

Every candidate must pass Move-expert verification before report inclusion:

- exact file, line, function, and root cause
- legitimate user story and attacker story
- concrete Sui PTB or Aptos transaction sequence
- reachability through public/entry paths
- capability/object/resource/signer feasibility
- math bounds with realistic token, TVL, timing, oracle, and precision ranges
- Move safety disproof: type system, abilities, ownership, visibility, no
  callbacks, no delegatecall, overflow-abort semantics
- economic impact: victim, amount or liveness consequence, and likelihood
- counterfactual fix test: recommended fix changes observable behavior
- root-cause deduplication and parallel subsystem check

Use labels from `verification-runner.md`: `confirmed`, `likely`,
`needs_review`, `dismissed`, `overclassified`, or `blocked`.

High/Critical findings require `confirmed` or `likely` confidence plus hard
evidence from `confidence-gates.md`. Pattern matches alone are capped at
`needs_review` and Medium.

## Build And Test Handling

If build tooling exists:

- Sui: run `sui move build`; when useful, run `sui move test`.
- Aptos: run `aptos move compile`; when useful, run `aptos move test`.

Capture command, exit code, and key logs in artifacts. If tooling or dependencies
are missing, write `resource-requests.json` and continue static analysis. Do not
convert missing tooling into a false negative.

## Reporting Rules

- Never hallucinate files, APIs, or behavior.
- Never report without exact code location.
- Never promote a finding from docs, comments, mocks, or pattern match alone.
- Never dismiss with weak evidence; use trusted code, tests, production source,
  production state, or a valid negative PoC.
- Separate confirmed, likely, needs-review, dismissed, blocked, and clean checks.
- Include optional context used, especially answer-bearing context, in the report.
- Keep progress artifacts current until the final report is written.
- State that AI-assisted results require human review before disclosure or use in
  bounty/private submissions.
