#!/usr/bin/env bash
set -euo pipefail

# Generate TypeScript types using typescript-json-schema if available
if command -v typescript-json-schema >/dev/null 2>&1; then
  typescript-json-schema --topRef --noExtraProps --strictNullChecks contracts/*.schema.json '*' > contracts/gen/ts/contracts.d.ts || true
else
  echo "[skip] typescript-json-schema not installed"
fi

# Generate Python Pydantic models using datamodel-code-generator if available
if command -v datamodel-codegen >/dev/null 2>&1; then
  datamodel-codegen \
    --input contracts/ \
    --input-file-type jsonschema \
    --output contracts/gen/py/models.py \
    --use-schema-description \
    --use-title-as-name || true
else
  echo "[skip] datamodel-codegen not installed"
fi
