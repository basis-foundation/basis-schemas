# Vocabulary Contract

The **vocabulary** contract is the first machine-readable contract published in
`basis-schemas`. It publishes the canonical BASIS action verbs decided in
`basis-architecture` (`docs/architecture/action-vocabulary.md`). It is a
publication, not a design: it does not invent, rename, or redefine verbs.

- Contract file: [`../schemas/vocabulary/vocabulary.yaml`](../schemas/vocabulary/vocabulary.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`

## The five canonical verbs

| Verb        | Meaning |
| ----------- | ------- |
| `read`      | Retrieve the current value, state, or configuration of a resource, without modification. |
| `write`     | Modify the value, setpoint, configuration parameter, or state of a resource. Absorbs structural configuration changes (no separate `configure` verb). |
| `execute`   | Cause the resource to perform an operation or command, as distinct from writing a value. |
| `browse`    | Enumerate or navigate the resource or address space without retrieving operational values. |
| `subscribe` | Establish a subscription to ongoing telemetry or event notifications from a resource. |

These five cover every operation emitted by all nine protocol adapters (BACnet,
Modbus, OPC UA, MQTT, DNP3, IEC 61850, KNX, Niagara, REST). New verbs are not
introduced here; they require Foundation review and an update to the governing
document in `basis-architecture`.

## Why `experimental`?

The lifecycle is `experimental` because this is the first published contract
format in `basis-schemas` and its consumption path is new — not because the
architectural vocabulary is unsettled. The verbs themselves are mature and
governed. The lifecycle describes the **published contract**, which advances to
`candidate` once real consumers exercise it and to `stable` only when
`basis-architecture` confirms the shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).

## Scope

This contract carries **verbs only**. The composite action-name format
`{verb}:{domain}[:{object}]` is a separate, later contract (`action-string`); see
[`migration-plan.md`](migration-plan.md).
