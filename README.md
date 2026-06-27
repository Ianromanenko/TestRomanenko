# TestRomanenko

## Skills

### `text-to-cad`

A Claude Code skill that generates 3D CAD models and mesh files from
natural-language descriptions using the [Zoo (KittyCAD) Text-to-CAD API](https://zoo.dev/docs/api/ml/generate-a-cad-model-from-text).

Ask Claude to "make a 3D model of …", "generate a STEP file of …", or "design a
…" and the skill submits the prompt, waits for the asynchronous generation job,
and writes the resulting model file(s) to disk.

**Supported formats:** STEP, STL, OBJ, PLY, glTF, GLB, FBX.

**Setup:** create an API token at <https://zoo.dev/account/api-tokens> and export
it before use:

```bash
export ZOO_API_TOKEN=...
```

**Direct usage of the bundled script:**

```bash
python3 .claude/skills/text-to-cad/scripts/text_to_cad.py \
  "a 2x4 lego brick" --format step --output ./models --name lego_brick
```

See [`.claude/skills/text-to-cad/SKILL.md`](.claude/skills/text-to-cad/SKILL.md)
for full details. The script uses only the Python 3 standard library.
