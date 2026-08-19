# Verification Runner

Use this file during verification and confirmation. It defines how findings move
from candidate to reportable status.

## Evidence Ladder

Order evidence from weakest to strongest:

1. Pattern match only.
2. Code evidence: exact missing or broken check in source.
3. Math proof: concrete bounds, realistic values, threshold table.
4. Existing test evidence: target's tests show the claimed behavior.
5. New local proof: added test or harness exercises the real vulnerable path.
6. Production read-only evidence: deployed package/object/config state proves a
   required precondition exists.

Do not use docs, comments, mocks, or external assumptions to dismiss a finding.

## Local Build And Test Commands

Use the project-native toolchain when available.

Sui:

- Build: `sui move build`
- Test: `sui move test`

Aptos:

- Build: `aptos move compile`
- Test: `aptos move test`

Rules:

- Build/test logs are evidence, not automatic findings.
- Use the exact production build, not a test build, to prove API exclusion.
- Review warnings for unknown or ignored attributes. Enumerate the emitted
  module's public/entry functions with the toolchain's bytecode disassembler or
  module inspector and compare them with the intended publish API.
- Treat source comments, function prefixes, and auxiliary-tool annotations as
  claims only. If a helper survives in bytecode, verify it as ordinary
  production code using its actual visibility and authorization.
- Use raw symbol searches only for discovery; require bytecode/API inspection to
  prove that a function exists, is public/entry, or is absent.
- A passing test proves only what the test asserts.
- A failing test may reveal a bug only when the failure matches the candidate's
  exact source location, precondition, and impact.
- Do not repeatedly retry missing dependency/toolchain failures. Record a
  `resource-requests.json` row and continue with static verification.

## Writing Local Proofs

When the user has not asked for code fixes, do not edit production source.
Prefer adding tests or harness files that can be removed later.

A local proof should:

- call the real target module/function;
- use only attacker-obtainable signers, objects, resources, and type arguments;
- construct the concrete precondition through valid protocol operations;
- assert the harmful postcondition;
- print or assert a clear success signal;
- avoid mocked trusted components unless the mocked behavior is something a real
  attacker can cause.

If the proof requires a trusted oracle, verifier, admin, or bridge to lie in a
way an attacker cannot cause, the finding is not confirmed.

## Sui Verification Notes

For Sui:

- Think in programmable transaction blocks for `public fun`.
- Confirm whether objects are owned, shared, immutable, wrapped, or frozen.
- A PTB cannot call `public(package)` functions.
- Runtime ownership is an access-control gate.
- Old package versions remain callable; check whether live shared objects carry
  version fields and whether every public surface asserts the current version.
- Denylist behavior for regulated coins is validator/runtime behavior; do not
  invent missing Move-level checks unless the epoch/receiving gap is relevant.
- Read-only production evidence may include package IDs, object IDs, object
  fields, package versions, and config values. Do not submit transactions.

## Aptos Verification Notes

For Aptos:

- `public fun` is not a transaction entry point unless it is also `entry`.
- `&signer` is not authorization by itself; authorization requires address or
  capability checks.
- Global resources and `acquires` can enforce exclusivity but do not prove
  business authorization.
- Block-STM ordering and mempool behavior matter for front-running and griefing.
- Read-only production evidence may include module address, resource state, and
  config values. Do not submit transactions.

## Promotion Rules

Promote a candidate to `confirmed` when:

- source evidence identifies the exact bug;
- reachability is concrete;
- the attacker path uses only real Move capabilities;
- impact names victim and value/liveness loss;
- one of these holds:
  - local proof runs against the real target path;
  - math proof plus code evidence satisfies hard evidence requirements;
  - production read-only state plus code evidence proves the precondition and
    exploit path.

Promote to `likely` when:

- source and math evidence are strong;
- exploit path is concrete;
- local proof is blocked by tooling or environment rather than by logic.

Keep as `needs_review` when:

- the idea is plausible;
- decisive proof is missing;
- High/Critical evidence requirements are not met.

Mark `dismissed` only when trusted evidence proves the exploit cannot work:

- exact source check blocks it;
- real type/ability/visibility/ownership rules block it;
- a local negative proof exercises the claimed path and shows no bug;
- production state makes the required precondition impossible.

Mark `overclassified` when the bug exists but the impact or likelihood is lower
than claimed.

## Mandatory Kill Questions

Before any finding reaches `confirmed` or `likely`, answer:

1. What exact public/entry path can the attacker call?
2. What signer/object/resource/capability does the attacker need?
3. How does the attacker obtain each prerequisite?
4. What invariant breaks?
5. Who loses money, authority, or liveness?
6. What concrete amount or operational impact is realistic?
7. Which Move rule could invalidate the attack, and why does it not?
8. Does the recommended fix change observable behavior?
9. Are there parallel call sites or subsystems with the same root cause?
10. Is this a known-good DeFi design pattern in this protocol's context?

If any answer is unknown, cap at `needs_review` unless the finding is deliberately
reported as a blocked but high-priority lead.

## Verification Output

For each candidate, write one row to `verification-results.json`. Then:

- `confirmed`, `likely`, and retained `needs_review` rows go to
  `confirmed-findings.json`.
- `dismissed` rows go to `dismissed-findings.json`.
- `overclassified` rows go to `confirmed-findings.json` with adjusted severity.
- `blocked` rows also create or update `resource-requests.json`.

## Reportability

Critical and High are reportable only when:

- reachability is `pass`;
- Move safety gate is `pass`;
- math bounds are `pass` or `not-applicable`;
- impact has a victim and realistic amount/liveness consequence;
- confidence is `confirmed` or `likely`;
- evidence includes `[CODE]` plus at least one independent strong signal such
  as `[TEST]`, `[MATH]`, `[PROD-STATE]`, or a concrete PTB/transaction proof.
