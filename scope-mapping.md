# Scope Mapping

Use this file during Surface Map. The goal is to produce a complete, concrete
`scopes.json` inventory before deep audit begins.

## Chain Detection

Classify the target:

- Sui: imports or references `sui::object`, `sui::transfer`,
  `sui::tx_context`, `UID`, `Clock`, `Coin<T>`, shared objects, or PTB-facing
  functions.
- Aptos: imports or references `aptos_framework`, `aptos_std`, `signer`,
  `account`, `coin`, `fungible_asset`, `timestamp`, or `#[test_only]`.
- Mixed: code, docs, or bridges reference both ecosystems.
- Unknown Move: `.move` code exists but chain-specific signals are weak.

## Entry Point Classification

Attack surface differs by chain:

| Visibility | Sui attack surface | Aptos attack surface |
| --- | --- | --- |
| `public entry fun` | PTB-callable and direct transaction | transaction entry |
| `public fun` | PTB-callable | module-callable only |
| `entry fun` | direct transaction only | transaction entry |
| `public(package) fun` | package-internal | package-internal |
| `fun` | private | private |

Critical Sui rule: a state-mutating `public fun` is an external attack surface
because a programmable transaction block can call it.

## Access Control Classification

For every public or entry function, assign one:

- `public-unrestricted`: shared object or global resource mutation with no
  signer/capability/owner gate.
- `capability-gated`: requires a role/cap object, signer cap, or stored cap.
- `owner-gated`: Sui owned object controls access by runtime ownership.
- `signer-gated`: Aptos signer address is checked against trusted state.
- `package-gated`: only package-internal callers can reach it.
- `review-required`: gate is unclear or depends on callers.

Any `public-unrestricted` state mutation is high priority.

## Required Scope Lenses

Apply all lenses. A scope may have multiple lenses.

### 1. Entrypoint Lens

Create a scope for every externally reachable function:

- Sui `public fun`, `entry fun`, `public entry fun`
- Aptos `entry fun`, `public entry fun`
- exposed bridge/message/handler functions
- public view/helper functions that feed signed quotes, liquidation decisions,
  health checks, exchange rates, or oracle values
- any public/entry helper found in the emitted production module but absent from
  the intended publish API, including source functions labeled for tests,
  verification, analysis, debugging, development, or mocks

### 2. Value-Flow Lens

Create scopes for every place value or accounting changes:

- mint, burn, split, join, deposit, withdraw, redeem, claim
- borrow, repay, liquidate, seize, ADL, bad debt, insurance
- share, LP, vault, reward, fee, debt, collateral, and index accounting
- internal ledger writes that must match actual `Coin<T>`/resource movement

### 3. Authority Lens

Create scopes for every authority boundary:

- capability structs, role maps, admin signers, guardians, multisig, thresholds
- package upgrade, pause/unpause, rescue, close/reclaim, migration
- setters for rate models, oracle config, collateral factors, fees, limits
- signer verification and policy versioning

### 4. State-Invariant Lens

Create scopes for persistent state that must stay coherent:

- `has key` structs
- Sui shared objects
- Aptos resources under global storage
- tables, bags, dynamic fields, vectors, VecMap/VecSet, object tables
- counters, indexes, epochs, timestamps, checkpoints, accumulators

### 5. Math Lens

Create scopes for:

- fixed-point helpers: `mul`, `div`, `from`, `to`, scaling conversions
- `WAD`, `RAY`, `Decimal`, `Float`, custom precision wrappers
- bit shifts, masks, packed fields, bucket math
- rate/fee/reward/interest/price math
- rounding, tick, lot-size, quote, and settlement conversions

### 6. Oracle And External Data Lens

Create scopes for:

- Pyth, Switchboard, custom oracle reads, TWAP/EMA/spot choice
- freshness, decimals, confidence/deviation, sign, zero/negative handling
- separate price reads used for check vs settlement
- source-chain messages, VAAs, bridge payloads, and recipient decoding

### 7. Composition Lens

Create scopes for relationships no single function can prove alone:

- deposit/withdraw symmetry
- borrow/repay symmetry
- liquidation trigger/seize consistency
- reward update before/after user operations
- admin config before/after interest accrual
- limiter add/reduce across time windows
- flash-loan receipt and mid-PTB accounting
- old package version calls against upgraded shared objects

## Scope Granularity

Make scopes small enough to audit deeply:

- Good: "reserve::liquidate collateral reserve cash check before split"
- Bad: "reserve module"
- Good: "reward_manager::update overflow before last_update checkpoint"
- Bad: "reward logic"

If a function has multiple independent obligations, split it into multiple
scopes. If one obligation spans files, list a region summary and include all
relevant files in `why`.

## Priority Scoring

Set `score` from 0 to 100:

- 90-100: direct fund loss, unauthorized mint/withdraw, permanent protocol
  deadlock, liquidation failure with bad debt, signer/policy bypass.
- 75-89: major liveness failure, stale package exploitability, oracle/price
  divergence, admin action that later bricks users.
- 55-74: partial fund loss, griefing with economic impact, medium confidence
  accounting break.
- 30-54: low impact, admin-gated, unlikely preconditions, integration risk.
- 0-29: informational, hardening, style, docs, or unreachable surfaces.

Score is not confidence. A high score means "audit this early", not "there is a
bug".

## Minimum Mapping Commands

Use fast local inspection before reading deeply:

- `rg --files`
- `rg -n "public( entry)? fun|entry fun|public\\(package\\) fun|struct .*has"`
- `rg -n "transfer::share_object|share_object|Clock|timestamp|signer::address_of"`
- `rg -n "borrow|repay|liquidat|seize|deposit|withdraw|claim|reward|oracle|price"`
- `rg -n "Decimal|Float|WAD|RAY|fixed|mul|div|MASK|SHIFT|bitmap|VecMap|VecSet"`
- `rg -n "ed25519|secp256k1|verify_signature|nonce|threshold|guardian"`
- `rg -n '#\[[^]]+\]'` followed by production bytecode/API enumeration when
  attributes are present

When `rg` is unavailable, use the fastest available alternative.

## Completeness Gate

Before leaving Surface Map:

- Every public/entry function is either a scope or intentionally covered by a
  larger concrete scope.
- Source entrypoint inventory is reconciled with the emitted production module;
  every unexpected surviving function is scoped by actual visibility.
- Every persistent state type has at least one lifecycle/invariant scope.
- Every capability/admin/signer boundary has a scope.
- Every value movement has a scope.
- Every fired checklist-router signal has at least one routed scope.
- Fixed-point helpers and call sites have scopes.
- Sui shared objects and old-package-version risk have scopes.
- Lending/staking/oracle/liquidation protocols have composition scopes.
