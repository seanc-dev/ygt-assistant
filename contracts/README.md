# Contracts

Versioned JSON Schemas defining shared data structures across the system. We generate language bindings for TypeScript (front-end) and Python (backend) to keep types consistent.

## Schemas
- `approval.schema.json`
- `draft.schema.json`
- `automation.schema.json`
- `note.schema.json`
- `core_memory.schema.json`

## Codegen
Run the generator to update bindings:

```bash
./scripts/gen_contracts.sh
```

Outputs:
- TypeScript types to `contracts/gen/ts/`
- Python Pydantic models to `contracts/gen/py/`

## Versioning
- Use semver in the `$id` and `version` fields.
- Backwards-compatible changes are minor versions.
- Breaking changes bump major; keep previous schemas until all consumers migrate.
