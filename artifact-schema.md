# Artifact Schema

All full autonomous runs write artifacts under `.move-auditor/`. JSON artifacts
must remain parseable so future runs can resume, diff, and verify coverage.
`progress.md`, `dashboard.html`, and `report.md` are human-readable derivatives
of the JSON state.

## `run.json`

```json
{
  "schema": "move-auditor.run.v1",
  "target": "string",
  "chain": "sui|aptos|mixed|unknown",
  "source_roots": ["sources"],
  "build_root": ".",
  "manifest_paths": ["Move.toml"],
  "docs": ["README.md"],
  "build": {
    "available": true,
    "command": "sui move build",
    "exit_code": 0,
    "summary": "short result"
  },
  "tests": {
    "available": true,
    "command": "sui move test",
    "exit_code": 0,
    "summary": "short result"
  },
  "operator_context": [
    {
      "source": "prompt|path",
      "classification": "scope|known_issue|threat_model|focus_area|out_of_scope|deployment|other",
      "summary": "string",
      "answer_bearing": false
    }
  ],
  "started_at": "ISO-8601 or unknown",
  "updated_at": "ISO-8601 or unknown"
}
```

## `progress.json`

```json
{
  "schema": "move-auditor.progress.v1",
  "run_status": "initializing|running|blocked|completed",
  "current_phase": "A|B|C|D|E|F|G",
  "phase_label": "Intake|Surface Map|Coverage Routing|Scope Audit|Cross-Scope Synthesis|Verification|Report",
  "phase_status": "pending|running|blocked|completed",
  "target": "string",
  "started_at": "ISO-8601 or unknown",
  "updated_at": "ISO-8601 or unknown",
  "active_scope": {
    "id": "SCOPE-001",
    "module": "string",
    "region": "sources/module.move:10-80",
    "summary": "short current audit focus"
  },
  "active_command": {
    "command": "sui move test",
    "status": "not-started|running|passed|failed|skipped",
    "summary": "short command result or current purpose"
  },
  "counts": {
    "scopes_total": 0,
    "scopes_audited": 0,
    "scopes_blocked": 0,
    "scopes_pending": 0,
    "candidates": 0,
    "confirmed": 0,
    "dismissed": 0,
    "clean_checks": 0,
    "resource_requests_open": 0
  },
  "phases": [
    {
      "id": "A",
      "label": "Intake",
      "status": "pending|running|blocked|completed",
      "summary": "phase result or current work"
    }
  ],
  "blockers": [
    {
      "id": "RES-001",
      "summary": "missing Sui CLI",
      "unblocks": ["verification"]
    }
  ],
  "latest_events": [
    {
      "time": "ISO-8601 or unknown",
      "level": "info|warning|error",
      "message": "short event"
    }
  ],
  "next_action": "string"
}
```

## `progress.md`

Human-readable mirror of `progress.json`. It must fit in one screen when
possible and include:

- run status, current phase, and last update time
- active scope and active command
- scope, candidate, verification, clean-check, and blocker counts
- phase checklist with `pending`, `running`, `blocked`, or `completed`
- latest events and next action

## `dashboard.html`

Self-contained browser dashboard generated from `progress.json`. It must:

- render without a local server;
- avoid external JavaScript, CSS, fonts, images, or network requests;
- auto-refresh when opened from disk so regenerated progress is visible;
- show the same status, counts, phase checklist, latest events, blockers, and
  next action as `progress.md`;
- be regenerated whenever `progress.json` changes.

Use `scripts/render_progress.py` when available. Resolve it relative to
`SKILL.md`, then pass the target project's `.move-auditor/progress.json`.

## `coverage-plan.json`

```json
{
  "schema": "move-auditor.coverage.v1",
  "chain": "sui|aptos|mixed|unknown",
  "signals": ["lending", "oracle", "fixed-point"],
  "loaded_references": ["common-move.md", "sui-patterns.md"],
  "feature_flags": [
    {
      "id": "fixed_point_helpers",
      "signal": "Decimal::mul",
      "required_followup": "fixed-point helper inspection"
    }
  ],
  "scope_routes": [
    {
      "scope_id": "SCOPE-001",
      "references": ["defi/defi-lending.md"],
      "checks": ["DEFI-25", "DEFI-80", "DEFI-90"]
    }
  ],
  "mandatory_passes": ["semantic-gap", "cross-module", "verification"]
}
```

## `scopes.json`

```json
[
  {
    "id": "SCOPE-001",
    "status": "pending|audited|blocked|needs-followup|deferred",
    "chain": "sui|aptos|mixed|unknown",
    "module": "module_name",
    "region": "sources/module.move:10-80",
    "kind": "entrypoint|value-flow|capability|shared-object|oracle|math|admin|bridge|signature|state-invariant|cleanup|integration",
    "obligation": "what this code must enforce",
    "attacker_surface": "who can reach it and how",
    "assets_at_risk": ["funds", "debt", "collateral"],
    "lenses": ["spec", "value-flow", "unbound-input", "ptb", "semantic-gap"],
    "exposure": "critical|high|medium|low",
    "difficulty": "high|medium|low",
    "score": 0,
    "assigned_checks": ["SUI-28", "DEFI-83"],
    "why": "short prioritization reason"
  }
]
```

## `candidate-findings.json`

```json
[
  {
    "id": "CAND-001",
    "scope_id": "SCOPE-001",
    "title": "string",
    "severity_claimed": "critical|high|medium|low|info",
    "category": "access-control|arithmetic|oracle|liquidation|accounting|signature|upgrade|dos|other",
    "location": "sources/module.move:42",
    "root_cause": "single root cause line or missing edge",
    "attacker": "attacker profile",
    "preconditions": ["concrete prerequisite"],
    "attack_steps": ["exact PTB or transaction step"],
    "impact": "who loses what",
    "evidence": [
      {
        "claim": "specific claim",
        "source": "file:line, command, or state read",
        "tag": "CODE|TEST|MOCK|DOC|EXT-UNVERIFIED|PROD-SOURCE|PROD-STATE|MATH"
      }
    ],
    "fix": "specific recommendation",
    "status": "candidate"
  }
]
```

## `verification-results.json`

```json
[
  {
    "candidate_id": "CAND-001",
    "verdict": "confirmed|likely|needs_review|dismissed|overclassified|blocked",
    "confidence": "confirmed|likely|needs_review",
    "final_severity": "critical|high|medium|low|info",
    "reachability": "pass|fail|unknown",
    "math_bounds": "pass|fail|not-applicable|unknown",
    "move_safety": "pass|fail",
    "economic_rationality": "pass|fail|not-applicable",
    "command_evidence": [
      {
        "command": "sui move test",
        "exit_code": 0,
        "matched": ["expected signal"],
        "log_summary": "short result"
      }
    ],
    "production_evidence": [],
    "reason": "decisive verification or dismissal reason"
  }
]
```

## `confirmed-findings.json`

Same base fields as `candidate-findings.json`, plus:

```json
{
  "verdict": "confirmed|likely|needs_review",
  "confidence": "confirmed|likely|needs_review",
  "final_severity": "critical|high|medium|low|info",
  "verification_summary": "why this survived",
  "command_evidence": [],
  "production_evidence": [],
  "parallel_instances": []
}
```

## `dismissed-findings.json`

```json
[
  {
    "candidate_id": "CAND-001",
    "title": "string",
    "dismissal_reason": "string",
    "decisive_evidence": [
      {
        "claim": "why exploit cannot work",
        "source": "file:line or command",
        "tag": "CODE|TEST|PROD-SOURCE|PROD-STATE"
      }
    ]
  }
]
```

## `clean-checks.json`

```json
[
  {
    "scope_id": "SCOPE-001",
    "check_id": "SUI-23",
    "status": "clean|not-applicable|blocked",
    "evidence": "file:line or command summary",
    "tag": "CODE|TEST|DOC|PROD-STATE",
    "notes": "short explanation"
  }
]
```

## `resource-requests.json`

```json
[
  {
    "id": "RES-001",
    "kind": "toolchain|dependency|network|artifact|deployment|credential|other",
    "priority": "high|medium|low",
    "needed": "Sui CLI",
    "reason": "required to run sui move test",
    "unblocks": ["verification", "SCOPE-001"],
    "status": "open|resolved|ignored"
  }
]
```

## Report Status Rules

- `progress.json`, `progress.md`, and `dashboard.html` must reflect the latest
  phase gate before the agent claims progress is visible in a UI.
- `candidate-findings.json` may contain unverified leads.
- `confirmed-findings.json` must not contain dismissed or blocked claims.
- `report.md` must distinguish `confirmed`, `likely`, and `needs_review`.
- High/Critical entries in `report.md` must cite a matching
  `verification-results.json` row.
