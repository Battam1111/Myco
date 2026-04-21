# Myco schema bundle

Machine-checkable schemas for substrate artefacts.

## `canon.schema.json`

JSON-Schema (2020-12 draft) describing the shape of `_canon.yaml`.
Governing doctrine:
[`../architecture/L1_CONTRACT/canon_schema.md`](../architecture/L1_CONTRACT/canon_schema.md).

### IDE integration

Most IDEs that understand JSON-Schema can validate YAML against it.

**VS Code** (`.vscode/settings.json`):

```json
{
  "yaml.schemas": {
    "https://raw.githubusercontent.com/Battam1111/Myco/main/docs/schema/canon.schema.json": [
      "_canon.yaml"
    ]
  }
}
```

**JetBrains** (Settings → Languages & Frameworks → Schemas and DSLs → JSON Schema Mappings):

- File or glob: `_canon.yaml`
- Schema URL: `https://raw.githubusercontent.com/Battam1111/Myco/main/docs/schema/canon.schema.json`

**Neovim** (via `yaml-language-server` / `nvim-lspconfig`):

```lua
require('lspconfig').yamlls.setup {
  settings = {
    yaml = {
      schemas = {
        ['https://raw.githubusercontent.com/Battam1111/Myco/main/docs/schema/canon.schema.json'] = '_canon.yaml',
      },
    },
  },
}
```

### What this schema enforces

The schema is a **second** mechanical check. It runs at edit time
(in the IDE) and catches:

- missing required top-level keys (`schema_version`, `contract_version`,
  `identity`, `system`, `subsystems`)
- malformed version strings
- `substrate_id` slug shape
- `lint.categories` set membership
- `rule_count` ≠ 7

The first (authoritative) check remains `myco.core.canon.load_canon`,
which runs at kernel import. The schema catches user-facing shape
errors before the kernel ever sees the file; the kernel catches
semantic drift the schema cannot model (schema upgraders, lockstep
sync_contract_version invariant, etc.).

### Kernel ↔ schema consistency

Changes to the kernel validator in `myco.core.canon` must be
mirrored here and vice versa. A future dimension (`SC1`
`schema-consistency`) is planned to lint this mirror; until then
the synchronisation is maintainer-discipline.

### Versioning

This schema's `$id` is pinned to `main`. When the canon schema
shape changes (contract bump), regenerate this file in the same
commit and land it through the normal `fruit + molt` governance
loop.
