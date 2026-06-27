---
name: text-to-cad
description: Generate 3D CAD models and mesh files from natural-language descriptions using the Zoo (KittyCAD) Text-to-CAD API. Use when the user wants to create, generate, or design a 3D model, CAD part, or printable geometry from a text prompt — e.g. "make a 3D model of a gear", "generate a STEP file of a bracket", "design a 2x4 lego brick", or to export STEP/STL/OBJ/PLY/glTF/GLB/FBX from a description.
---

# Text-to-CAD

Turn a text description into a real 3D CAD model using Zoo's Text-to-CAD API. The
API runs a generation job asynchronously and returns the model file(s) base64
encoded; the bundled script handles job creation, polling, and writing decoded
files to disk.

## Prerequisites

- A Zoo API token in the `ZOO_API_TOKEN` environment variable. The user creates
  one at https://zoo.dev/account/api-tokens. If it is missing, ask the user to
  set it before running (`export ZOO_API_TOKEN=...`). Never hard-code or print
  the token.
- Python 3 (standard library only — no pip install needed).

## How to use

Run the bundled script with the prompt and desired output format:

```bash
python3 scripts/text_to_cad.py "<description>" --format <format> --output <dir> --name <basename>
```

Example — generate a STEP file of a lego brick into `./models`:

```bash
python3 .claude/skills/text-to-cad/scripts/text_to_cad.py \
  "a 2x4 lego brick" --format step --output ./models --name lego_brick
```

The script submits the prompt, polls until the job reaches `completed` or
`failed`, then decodes and writes the resulting file(s). It prints the paths of
everything it wrote.

### Options

- `--format`, `-f`: one of `step`, `stl`, `obj`, `ply`, `gltf`, `glb`, `fbx`.
  Default `step`. Pick by use case:
  - `step` — parametric/solid CAD interchange (most CAD software). Good default.
  - `stl` — 3D printing / slicers.
  - `obj`, `ply`, `gltf`, `glb`, `fbx` — meshes for rendering / visualization.
- `--output`, `-o`: directory to write into (created if needed). Default `.`.
- `--name`, `-n`: base filename (extension is added automatically).
- `--project-name`: optional project label sent to the API.
- `--timeout`: max seconds to wait for the job (default 600).
- `--save-kcl`: also write the generated KCL source (`.kcl`) Zoo used to build
  the model — handy for editing the parametric model afterward.

## Guidance for good prompts

Text-to-CAD works best with clear, concrete mechanical descriptions and explicit
dimensions/units. Prefer e.g. "a flat washer, 20mm outer diameter, 8mm inner
diameter, 2mm thick" over vague requests. If the user's request is vague, ask one
clarifying question about dimensions or intended use, or pass it through as-is and
note that adding dimensions improves results.

## Notes

- Generation is asynchronous and can take from a few seconds to a couple of
  minutes; the script polls automatically.
- On failure the API returns a `failed` status with an error message (often the
  prompt couldn't be turned into valid geometry) — relay it and suggest a more
  specific prompt.
- The default output always includes the requested format; the script writes
  every file returned in the job's `outputs`.

## API reference

- Create: `POST https://api.zoo.dev/ai/text-to-cad/{output_format}` with JSON body
  `{"prompt": "..."}` and header `Authorization: Bearer $ZOO_API_TOKEN`.
- Poll: `GET https://api.zoo.dev/user/text-to-cad/{id}` until `status` is
  `completed` or `failed`. The `outputs` map holds `{filepath: base64}`.
- Docs: https://zoo.dev/docs/api/ml/generate-a-cad-model-from-text
