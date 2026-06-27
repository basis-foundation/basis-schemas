# Migration Plan

This document records the order in which existing contracts migrate into
`basis-schemas`, and which contracts are deliberately deferred. It follows the
initial migration candidates decided in `basis-architecture`
(`docs/architecture/basis-schemas.md`, §8 and §9). The ordering is a plan, not a
commitment: the actual sequence is confirmed contract by contract as each is
decided ready in `basis-architecture`.

The **vocabulary** contract has been published (see
[`../schemas/vocabulary/vocabulary.yaml`](../schemas/vocabulary/vocabulary.yaml)).
It is the first machine-readable contract in `basis-schemas`; the remaining
contracts below are still placeholders.

---

## Migration order

Contracts migrate in dependency-and-stability order, lowest-risk first:

1. **Vocabulary** — ✅ **published** (`experimental`). The five canonical action
   verbs (`read`, `write`, `execute`, `browse`, `subscribe`). The smallest,
   most-settled contract, already governed by a mature document in
   `basis-architecture`. Migrating it first proves the publish-and-consume
   mechanism on low-risk content and lets the provisional `basis-console`
   vocabulary copy be retired.
2. **Action string** — ⬅ **next planned**. The composite action-name format
   `{verb}:{domain}[:{object}]`. Depends only on the vocabulary; it is the format
   that wraps the verbs. Stable in `basis-core` today.
3. **Resource identifier** — the canonical typed identifier `{type}:{qualifier}`.
   The parallel format contract, also stable in `basis-core`. Together with the
   action string it covers the two canonical identifier shapes.
4. **Decision request** — the kernel input: subject, composite action, optional
   canonical resource identifier, and context. Composes the action string and
   resource identifier, so it can only follow once both formats are published.
5. **Decision response** — the kernel output: outcome, reason, evaluating policy,
   policy version, optional failure reason, and timestamp. Pairs with the request
   and is independently stable.
6. **Audit event** — the canonical audit structure, including its schema version
   and action-vocabulary version field. Last of this set because it is the
   broadest — it references action, resource, and policy version — and its
   surrounding pipeline is still emerging. Migrating the *shape* is safe, but it
   benefits from the earlier contracts being settled first.

```text
1. vocabulary           ✅ published (experimental)
2. action-string        ⬅ next planned (depends on vocabulary)
3. resource-identifier  (parallel format)
4. decision-request     (composes action-string + resource-identifier)
5. decision-response    (pairs with decision-request)
6. audit-event          (references action, resource, policy version)
```

Each contract is published first as **experimental**, advances to **candidate**
once exercised by real consumers, and becomes **stable** only when
`basis-architecture` confirms the shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md) for the state definitions.

## Deferred contracts

The following are strong candidates but are intentionally **not** in the first
wave. They are deferred because they are either more complex, depend on an
unresolved architecture question, or are better introduced once the core six
establish the repository's conventions:

- **Normalized request shape** — the adapter/console normalization shape
  (`action`, `resource_type`, `resource_id`, `context`/`evidence`). Deferred
  because it depends on the still-open action-domain vs resource-type question.
- **Reserved evidence namespace rule** — the rule that the `basis_gateway.*`
  namespace is reserved and callers must not write to it. Deferred until the core
  six establish conventions; the gateway's *enforcement* of the rule always stays
  in the gateway.
- **Compatibility snapshots** — cross-repository validation fixtures. Deferred
  until there are published contracts to snapshot against.
- **Schema versioning metadata format** — generalized version/compatibility
  identifiers. Introduced alongside the first contracts rather than ahead of them.

## Contracts that do not migrate

Some contracts named in the inventory are **not** ready to be shared and remain
open architecture questions owned by `basis-architecture` until implementation
proves a stable shape. They must not be formalized here yet, because doing so
would bake in a decision before the constraints that should shape it are
understood:

```text
resource taxonomy
action-domain vs resource-type distinction
audit persistence
deployment trust relationships
operator workflows
policy lifecycle governance
```

When any of these stabilizes into a shape multiple components must agree on, it
may graduate into the migration plan. Until then, this repository neither defines
nor anticipates them.

## Why complex contracts are deferred

The deferral is deliberate, not incidental. The core six are the smallest, most
settled, most independently stable contracts in the ecosystem; migrating them
first proves the publish-and-consume mechanism on low-risk content and
establishes the repository's conventions before any contentious shape is
formalized. The deferred contracts each carry an unresolved dependency — an open
architecture question, a need for prior contracts to exist, or a pipeline that is
still emerging — and formalizing them early would publish an unstable shape as if
it were settled. Holding them back keeps `basis-schemas` true to its charter:
publish decided contracts, do not invent shapes ahead of the architecture that
governs them.
