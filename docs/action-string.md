# Action String Contract

The **action string** contract is the second machine-readable contract published
in `basis-schemas`. It publishes the composite action-name format decided in
`basis-architecture` (`docs/architecture/action-vocabulary.md`) and enforced
today by `basis-core`. It is a publication, not a parser: it defines the shape, it
does not implement validation behavior.

- Contract file: [`../schemas/action-string/action-string.yaml`](../schemas/action-string/action-string.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`vocabulary`](vocabulary.md)

## Structure

```text
{verb}:{domain}[:{object}]
```

An action string is two or three colon-separated lowercase segments:

| Segment  | Required | Meaning |
| -------- | -------- | ------- |
| `verb`   | yes      | The operation requested. One of the canonical verbs published by the vocabulary contract. |
| `domain` | yes      | The functional domain or system category that owns the resource. |
| `object` | no       | The specific resource object within the domain; non-empty when present. |

Each segment matches `^[a-z][a-z0-9_-]*$` — a lowercase letter followed by
lowercase letters, digits, hyphens, or underscores. The full string matches:

```text
^[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*(:[a-z][a-z0-9_-]*)?$
```

## Examples

Valid: `read:ahu`, `write:setpoint`, `execute:command`, `read:hvac:setpoint`,
`write:hvac:setpoint`, `read:audit:log`.

Invalid: `read` (no domain), `read:` (empty domain), `:ahu` (empty verb),
`read::setpoint` (empty middle segment), `read:ahu:setpoint:extra` (a fourth
segment — the object may not be subdivided).

## Dependency on the vocabulary contract

This contract publishes the **shape** of an action string; it does not enumerate
the verbs. The verb segment draws its allowed values from the
[vocabulary contract](vocabulary.md), which is why the contract declares
`depends_on: [vocabulary]`. A string can be structurally well-formed under this
contract yet use a verb the vocabulary does not publish; full validity requires
both the structure (here) and a recognized verb (there). Keeping the two separate
means the verb set can grow under vocabulary governance without restating the
format.

## Relationship to `basis-core`

`basis-core` enforces this format at runtime in its action validator. Its regex
accepts two-*or-more* segments as a permissive superset; this contract publishes
the architecture's canonical `{verb}:{domain}[:{object}]` structure, which caps
the object at a single optional segment. Where they differ, `basis-architecture`
governs, and this published shape is the canonical one consumers should target.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not the maturity of the format itself, which is settled and in
production use. It advances to `candidate` once real consumers exercise it and to
`stable` only when `basis-architecture` confirms the shape as a durable
commitment. See [`contract-governance.md`](contract-governance.md).
