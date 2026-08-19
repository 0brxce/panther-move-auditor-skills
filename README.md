<p align="center">
  <strong>move-auditor</strong><br>
  <em>Codex and Claude Code skill for Move smart contract security auditing</em>
</p>

<p align="center">
  <a href="https://opensource.org/license/mit/"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg" alt="Contributions Welcome"></a>
  <img src="https://img.shields.io/badge/version-4.0.0-blue.svg" alt="Version 4.0.0">
  <img src="https://img.shields.io/badge/patterns-180%2B-red.svg" alt="180+ Patterns">
  <img src="https://img.shields.io/badge/chains-Sui%20%7C%20Aptos-purple.svg" alt="Sui | Aptos">
</p>

<p align="center">
  Built by <a href="https://x.com/thepantherplus">Panther</a>
</p>

---

A portable skill for Codex and [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that turns your AI coding agent into an autonomous Move (Sui & Aptos) smart contract security auditor — battle-tested vulnerability patterns, artifact-backed coverage, and verification gates ready to run the moment you open a `.move` file.

**Read the full write-up:** [The Move Auditor — Blog Post](https://pantheraudits.com/blog/the-move-auditor.html)

---

## Features

- **180+ vulnerability patterns** across chain-agnostic, Sui-specific, Aptos-specific, and DeFi checks
- **Auto-activates** on `.move` files — no setup, no slash commands needed
- **Autonomous audit workflow** — intake, surface mapping, coverage routing, scope audit, synthesis, verification, and report
- **Machine-readable run artifacts** — scopes, coverage plan, candidate findings, verification results, clean checks, and report under `.move-auditor/`
- **Optional upfront context** — users can provide known issues, focus areas, threat model notes, package IDs, or out-of-scope rules without making context mandatory
- **Anti-false-positive engine** — confidence gating, evidence chains, FP catalog, and self-hallucination checks
- **Build & test log analysis** — catches arithmetic aborts, assertion failures, and `#[expected_failure]` anomalies
- **Signal-based coverage routing** — detects protocol type and loads only relevant patterns
- **DeFi deep-dive** — 90+ patterns covering staking, oracles, lending, liquidation, slippage, auctions, and signatures
- **Semantic gap detection** — stale state, accumulator drift, cross-module accounting desync
- **Real-world validated** — findings accepted into production codebases (see below)

---

## Install

### Codex

```bash
git clone https://github.com/pantheraudits/move-auditor.git
mkdir -p ~/.codex/skills
cp -r move-auditor ~/.codex/skills/move-auditor
```

Restart Codex after installing or updating so it reloads the skill index.

**Update to latest:**
```bash
cd move-auditor && git pull
rm -rf ~/.codex/skills/move-auditor
cp -r . ~/.codex/skills/move-auditor
```

### Claude Code

```bash
git clone https://github.com/pantheraudits/move-auditor.git
mkdir -p ~/.claude/commands
cp -r move-auditor ~/.claude/commands/move-auditor
```

Restart Claude Code after installing or updating so it reloads the command.

**Update to latest:**
```bash
cd move-auditor && git pull
rm -rf ~/.claude/commands/move-auditor
cp -r . ~/.claude/commands/move-auditor
```

---

## Usage

### Run an autonomous audit

From the root of the Move project under review:

```bash
cd /path/to/your-move-project
codex
```

Then run:

```text
Use $move-auditor to run a full autonomous audit of this Move codebase.
```

For Claude Code:

```text
/move-auditor
```

The auditor will create or resume `.move-auditor/`, map the attack surface, route
checks, audit scopes, verify candidates, show progress through `.move-auditor/`
progress artifacts, and write `.move-auditor/report.md`.

To resume a previous autonomous run:

```text
Use $move-auditor to continue the autonomous audit from existing `.move-auditor/` artifacts.
```

### Live progress UI

Full autonomous runs maintain these files while the audit is running:

- `.move-auditor/progress.json` - machine-readable phase and count state
- `.move-auditor/progress.md` - compact text dashboard for quick inspection
- `.move-auditor/dashboard.html` - browser-openable progress dashboard

The Markdown and HTML views are generated from `progress.json` by
`scripts/render_progress.py` when the script is available to the active skill.

Ask for progress explicitly when you want the dashboard surfaced during the run:

```text
Use $move-auditor to run a full autonomous audit of this Move codebase and show live progress in the progress UI.
```

The agent must not claim progress is visible in a UI unless `progress.md`,
`dashboard.html`, or a real control-plane URL exists.

### Codex

```bash
# 1. Navigate to your Move project
cd /path/to/your-move-project

# 2. Start Codex
codex
```

Then ask Codex:

```text
Use $move-auditor to audit this Move codebase.
```

You can also ask naturally, for example:

```text
Audit this Sui Move package for exploitable security issues.
```

### Claude Code

> `/move-auditor` is a slash command inside Claude Code — not a terminal command.
> Run it from within a Claude Code session.

```bash
# 1. Navigate to your Move project
cd /path/to/your-move-project

# 2. Start Claude Code
claude

# 3. Inside the session, run:
/move-auditor              # Full audit of all .move files in scope
/move-auditor [file]       # Audit a specific file
```

### Best results

For the deepest analysis, run the skill against a **buildable project** — one where
`sui move build` (Sui) or `aptos move compile` (Aptos) succeeds. The auditor will run
the test suite, capture logs, and analyze them for arithmetic aborts, assertion failures,
and suspicious `#[expected_failure]` annotations that may indicate latent High/Critical
bugs invisible to static-only review.

> **Static-only mode:** If the project doesn't build (missing deps, partial code, review-only
> context), the skill still runs the full pattern-based audit — it just skips test log analysis.

### Optional audit context

The autonomous scan does not require hand-fed hints, but users can provide extra context at
the start when they want a focused or informed run:

```text
Use $move-auditor to audit this Sui package.

Audit Context:
- Known issue: reward index sync was recently patched; verify old package versions.
- Focus area: liquidation and oracle settlement paths.
- Out of scope: admin-only parameter tuning with no user impact.
- Deployment: package 0x..., shared pool object 0x...
```

The same context can live in `.move-auditor/context.md`, `audit-context.md`,
`security-context.md`, or `known-issues.md`. Answer-bearing context is recorded in
`run.json` and treated as a lead for targeted verification, not as proof.

---

## How It Works

The skill runs an autonomous, resumable workflow on every full audit:

```
Intake          Detect chain, build root, docs, optional context, build/test state
     |
Progress UI     Refresh `.move-auditor/progress.*` and dashboard at phase gates
     |
Surface Map     Write `.move-auditor/scopes.json` for all concrete attack surfaces
     |
Coverage Router Load relevant Move/Sui/Aptos/DeFi references and attach checks
     |
Scope Audit     Audit one scope at a time; write candidates and clean checks
     |
Synthesis       Compose cross-module, PTB, stale-state, oracle, and package-version chains
     |
Verification    Confirm, downgrade, dismiss, or block every candidate with evidence gates
     |
Report          Generate `.move-auditor/report.md` from evidence-backed findings
```

Reference files are loaded **on demand** — the agent reads only what's relevant to the
detected chain, protocol type, and current phase while retaining machine-readable
artifacts for coverage and resume.

---

## Pattern Coverage

| Category | File | Patterns |
|----------|------|----------|
| Chain-agnostic | `common-move.md` | Access control, arithmetic, resource safety, logic, input validation, cross-module, upgradeability, build/test analysis |
| Sui-specific | `sui-patterns.md` | SUI-01 to SUI-46 |
| Aptos-specific | `aptos-patterns.md` | APT-01 to APT-25 |
| DeFi cross-cutting | `defi-vectors.md` | DEFI-01 to DEFI-10 |
| Staking & yield | `defi/defi-staking.md` | DEFI-11 to DEFI-16, DEFI-88 |
| Oracles | `defi/defi-oracle.md` | DEFI-17 to DEFI-24, DEFI-95 |
| Lending & borrowing | `defi/defi-lending.md` | DEFI-25 to DEFI-34, DEFI-80, DEFI-82, DEFI-84, DEFI-90, DEFI-93 |
| Math & precision | `defi/defi-math-precision.md` | DEFI-35 to DEFI-42, DEFI-85 to DEFI-87, DEFI-92 |
| Slippage & MEV | `defi/defi-slippage.md` | DEFI-43 to DEFI-49 |
| Liquidation | `defi/defi-liquidation.md` | DEFI-50 to DEFI-66, DEFI-81, DEFI-83, DEFI-91, DEFI-94 |
| Auctions & CLM | `defi/defi-auction-clm.md` | DEFI-67 to DEFI-73 |
| Signatures | `defi/defi-signatures.md` | DEFI-74 to DEFI-79, DEFI-89 |

---

## Skill Structure

```
move-auditor/
├── SKILL.md                          # Compact orchestrator — autonomous workflow routing
├── autonomous-workflow.md            # Phase gates, run loop, optional context, artifacts
├── artifact-schema.md                # JSON schemas for `.move-auditor/` outputs
├── scope-mapping.md                  # Move-specific surface inventory and scoring
├── verification-runner.md            # Sui/Aptos proof, build/test, and promotion rules
├── scripts/render_progress.py        # Progress Markdown and HTML dashboard renderer
│
├── common-move.md                    # Chain-agnostic checks + verification checklist
├── sui-patterns.md                   # Sui-specific patterns (SUI-01 to SUI-46)
├── aptos-patterns.md                 # Aptos-specific patterns (APT-01 to APT-25)
│
├── checklist-router.md               # Signal-based coverage planner & file router
├── verification-policy.md            # Evidence hierarchy, feasibility gates, severity discipline
├── semantic-gap-checks.md            # Stale-state, accumulator, cross-module desync checks
│
├── move-fp-catalog.md                # Anti-FP: rationalizations to reject, FP catalog
├── evidence-chains.md                # Structured evidence templates (verification phase)
├── confidence-gates.md               # Confidence gating, hard evidence requirements (verification phase)
│
├── defi-vectors.md                   # DeFi attack vectors (DEFI-01 to DEFI-10) + router
├── defi/
│   ├── defi-staking.md               # Staking/yield (DEFI-11 to DEFI-16, 88)
│   ├── defi-oracle.md                # Oracles (DEFI-17 to DEFI-24, DEFI-95)
│   ├── defi-lending.md               # Lending/borrowing (DEFI-25 to DEFI-34, 80, 82, 84, 90, 93)
│   ├── defi-math-precision.md        # Math & precision (DEFI-35 to DEFI-42, 85-87, 92)
│   ├── defi-slippage.md              # Slippage & DEX (DEFI-43 to DEFI-49)
│   ├── defi-liquidation.md           # Liquidation (DEFI-50 to DEFI-66, 81, 83, 91, 94)
│   ├── defi-auction-clm.md           # Auctions & CLM (DEFI-67 to DEFI-73)
│   ├── defi-signatures.md            # Signatures (DEFI-74 to DEFI-79, DEFI-89)
│   └── defi-lending-design-patterns.md  # Known-good patterns (DESIGN-L1 to L4)
│
├── audit-prompts.md                  # Deep-dive prompts & vulnerability pattern pack
├── sample-finding.md                 # Example audit output format
│
└── benchmarks/
    ├── BENCHMARK.md                  # Benchmarking methodology
    ├── BENCHMARK-openzeppelin.md     # OpenZeppelin contracts-sui benchmark
    └── BENCHMARK-currensui.md        # CurrenSui lending protocol benchmark
```

---

## Real-World Impact

Bugs found by `move-auditor` have been accepted into production codebases, contest leaderboards, and paid bug bounties. In every case the skill surfaced the *candidate* finding — a human auditor reproduced, narrowed, and wrote up the bug before submission.

| Context | Finding | Outcome |
|---------|---------|---------|
| Aptos perps protocol (private bug bounty, name withheld) | 1 High and 2 Medium findings accepted across private bounty reviews. Details withheld under program confidentiality; each candidate was surfaced with `move-auditor`, then reproduced, narrowed, and written up manually by [Panther](https://x.com/thepantherplus). | **24,000 USDC total accepted rewards** — 1 High + 2 Medium; private details withheld |
| [Current Finance](https://audits.sherlock.xyz/contests/current-finance) — Sherlock contest, Sui Move lending protocol | 1 High + 2 Medium confirmed findings: opposite-direction EMA/spot deviations creating unliquidatable positions, ADL using reserve-level instead of emode-group-level debt, deposit cap double-subtraction bypass. Identified with `move-auditor`, manually verified by [Panther](https://x.com/thepantherplus). | **#27 out of 170+ participants** |
| [OpenZeppelin Contracts for Sui](https://github.com/OpenZeppelin/contracts-sui) | Missing `EDivideByZero` guard in fixed-point `div`/`mod` — relied on opaque VM abort instead of descriptive error | [PR #263](https://github.com/OpenZeppelin/contracts-sui/pull/263) **Merged** |
| Sui DeFi margin protocol (bug bounty, name withheld) | Missing post-trade health check in margin trading proxy — leveraged accounts can keep trading after becoming liquidatable, enabling value extraction to a second account and leaving bad debt for lenders | **Confirmed** (duplicate of prior report) |
| Multiple Sui & Aptos protocols (bug bounties, names withheld) | Several additional findings across Sui and Aptos programs surfaced by `move-auditor` and manually reproduced and written up by [Panther](https://x.com/thepantherplus) | **In triage** — awards pending |

> The OpenZeppelin find was a unique result from [benchmarking](benchmarks/BENCHMARK-openzeppelin.md) — no other AI audit tool (MAIA, Raw Claude CLI) caught it.
>
> **How to read this table**: `move-auditor` now produces artifact-backed candidates and verification evidence, but it is still not a substitute for human sign-off. Each accepted row involved human reproduction, triage, and submission.

---

## Benchmarks

The skill is [benchmarked](benchmarks/BENCHMARK.md) against baseline prompts (raw Claude, MAIA) and manual review to measure where it actually makes a difference. Benchmark results drove multiple improvements:

- **v2.3.0 → v3.0.0**: CurrenSui detection improved from 2/6 to 4/6 known bugs + 2 novel findings
- **v3.4.0**: Anti-FP overhaul reduced false positive rate after [CurrenSui benchmark](benchmarks/BENCHMARK-currensui.md) revealed ~25% FP rate
- **v3.5.0**: 16 new Sui patterns from design-level anti-pattern analysis
- **v3.6.x**: Patterns validated against Current Finance contest — 1 High + 2 Medium confirmed, #27 placement

---

## Roadmap

- [ ] Vulnerability database (real-world Move CVEs and contest findings)
- [ ] Sui DeFi protocol-specific patterns (Cetus, Aftermath, Turbos)
- [ ] Aptos DeFi protocol-specific patterns (Thala, Aries, Echelon)
- [ ] Automated grep patterns for common Move anti-patterns
- [x] Machine-readable audit artifacts (`coverage-plan`, scopes, validated findings, structured clean checks)
- [x] Report template for autonomous audit output
- [x] Benchmarking against baseline prompts and manual review

---

## Disclaimer

AI-assisted audit output **must be manually verified**. This skill accelerates your workflow — it does not replace deep manual review and PoC testing. All findings require human confirmation before being included in any report.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Contact

Panther Audits — [GitHub](https://github.com/pantheraudits) · [Telegram](https://t.me/theblackpantherhere) · [X](https://x.com/thepantherplus)
