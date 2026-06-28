# Migration Plan

This document records the order in which existing contracts migrate into
`basis-schemas`, and which contracts are deliberately deferred. It follows the
initial migration candidates decided in `basis-architecture`
(`docs/architecture/basis-schemas.md`, §8 and §9). The ordering is a plan, not a
commitment: the actual sequence is confirmed contract by contract as each is
decided ready in `basis-architecture`.

The **vocabulary**, **action-string**, **resource-identifier**,
**decision-request**, and **decision-response** contracts have been published (see
[`../schemas/vocabulary/vocabulary.yaml`](../schemas/vocabulary/vocabulary.yaml),
[`../schemas/action-string/action-string.yaml`](../schemas/action-string/action-string.yaml),
[`../schemas/resource-identifier/resource-identifier.yaml`](../schemas/resource-identifier/resource-identifier.yaml),
[`../schemas/decision-request/decision-request.yaml`](../schemas/decision-request/decision-request.yaml),
and
[`../schemas/decision-response/decision-response.yaml`](../schemas/decision-response/decision-response.yaml)).
They are the first five machine-readable contracts in `basis-schemas`; the
remaining contract below (the audit event) is still a placeholder.

---

## Migration order

Contracts migrate in dependency-and-stability order, lowest-risk first:

1. **Vocabulary** — ✅ **published** (`experimental`). The five canonical action
   verbs (`read`, `write`, `execute`, `browse`, `subscribe`). The smallest,
   most-settled contract, already governed by a mature document in
   `basis-architecture`. Migrating it first proves the publish-and-consume
   mechanism on low-risk content and lets the provisional `basis-console`
   vocabulary copy be retired.
2. **Action string** — ✅ **published** (`experimental`). The composite
   action-name format `{verb}:{domain}[:{object}]`. Depends only on the
   vocabulary; it is the format that wraps the verbs. Stable in `basis-core`
   today.
3. **Resource identifier** — ✅ **published** (`experimental`). The canonical typed
   identifier `{resource_type}:{local_resource_id}`. The parallel format contract,
   also stable in `basis-core`. Together with the action string it covers the two
   canonical identifier shapes. Adapters emit the resource type and local resource
   id separately; the gateway composes them; the kernel consumes the composed
   identifier and derives the type from its prefix.
4. **Decision request** — ✅ **published** (`experimental`). The kernel input:
   subject (carried as flat `subject_id` / `subject_roles` / `subject_attrs`
   fields, matching `basis-core`), composite action, optional canonical resource
   identifier, and context. Composes the action string and resource identifier,
   which is why it follows once both formats are published. Stable in `basis-core`
   today; expects an already-composed request (canonical action and resource
   identifier), not adapter-local fields.
5. **Decision response** — ✅ **published** (`experimental`). The kernel output:
   an explicit `outcome` (allow / deny / not_applicable), reason, evaluating
   policy (`evaluated_by`), policy version, optional failure reason, and
   timestamp. Echoes the request's `request_id`, so it declares `depends_on:
   [decision-request]`. Pairs with the request and is independently stable in
   `basis-core` today.
6. **Audit event** — the canonical audit structure, including its schema version
   and action-vocabulary version field. Last of this set because it is the
   broadest — it references action, resource, and policy version — and its
   surrounding pipeline is still emerging. Migrating the *shape* is safe, but it
   benefits from the earlier contracts being settled first.

```text
1. vocabulary           ✅ published (experimental)
2. action-string        ✅ published (experimental) (depends on vocabulary)
3. resource-identifier  ✅ published (experimental) (parallel format)
4. decision-request     ✅ published (experimental) (composes action-string + resource-identifier)
5. decision-response    ✅ published (experimental) (pairs with decision-request)
6. audit-event          ⬅ next planned (references action, resource, policy version)
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
