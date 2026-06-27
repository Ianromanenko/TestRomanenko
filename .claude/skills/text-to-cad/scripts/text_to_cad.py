#!/usr/bin/env python3
"""Generate a 3D CAD model from a text prompt using the Zoo (KittyCAD) Text-to-CAD API.

Creates a text-to-CAD job, polls until it finishes, then decodes and writes the
resulting model file(s) to disk. Uses only the Python standard library.

Usage:
    export ZOO_API_TOKEN=...   # from https://zoo.dev/account/api-tokens
    python3 text_to_cad.py "a 2x4 lego brick" --format step --output ./models

Docs: https://zoo.dev/docs/api/ml/generate-a-cad-model-from-text
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_BASE = os.environ.get("ZOO_API_BASE", "https://api.zoo.dev")
FORMATS = ["step", "stl", "obj", "ply", "gltf", "glb", "fbx"]
TERMINAL = {"completed", "failed"}


def _request(method, path, token, body=None):
    url = API_BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise SystemExit(f"API error {e.code} on {method} {path}: {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error reaching {url}: {e.reason}")


def create(prompt, output_format, token, project_name=None):
    body = {"prompt": prompt}
    if project_name:
        body["project_name"] = project_name
    return _request("POST", f"/ai/text-to-cad/{output_format}", token, body)


def poll(job_id, token, timeout=600, interval=4):
    deadline = time.time() + timeout
    while True:
        job = _request("GET", f"/user/text-to-cad/{job_id}", token)
        status = job.get("status")
        if status in TERMINAL:
            return job
        if time.time() > deadline:
            raise SystemExit(f"Timed out after {timeout}s (last status: {status})")
        print(f"  status: {status} ...", file=sys.stderr)
        time.sleep(interval)


def main():
    ap = argparse.ArgumentParser(description="Generate a CAD model from text via the Zoo API.")
    ap.add_argument("prompt", help="Text description of the part to generate.")
    ap.add_argument("--format", "-f", default="step", choices=FORMATS,
                    help="Output file format (default: step).")
    ap.add_argument("--output", "-o", default=".", help="Directory to write output files into.")
    ap.add_argument("--name", "-n", default=None,
                    help="Base filename (without extension) for the written model.")
    ap.add_argument("--project-name", default=None, help="Optional project name passed to the API.")
    ap.add_argument("--timeout", type=int, default=600, help="Max seconds to wait (default: 600).")
    ap.add_argument("--save-kcl", action="store_true", help="Also write the generated KCL source (.kcl).")
    args = ap.parse_args()

    token = os.environ.get("ZOO_API_TOKEN")
    if not token:
        raise SystemExit("ZOO_API_TOKEN is not set. Create one at https://zoo.dev/account/api-tokens")

    print(f"Submitting prompt ({args.format}): {args.prompt}", file=sys.stderr)
    job = create(args.prompt, args.format, token, args.project_name)
    job_id = job["id"]
    print(f"Job {job_id} queued; polling...", file=sys.stderr)

    job = poll(job_id, token, timeout=args.timeout)

    if job.get("status") == "failed":
        raise SystemExit(f"Generation failed: {job.get('error') or 'unknown error'}")

    outputs = job.get("outputs") or {}
    if not outputs:
        raise SystemExit("Job completed but returned no outputs.")

    os.makedirs(args.output, exist_ok=True)
    written = []
    for path, b64 in outputs.items():
        ext = os.path.splitext(path)[1] or f".{args.format}"
        fname = (args.name + ext) if args.name else os.path.basename(path)
        dest = os.path.join(args.output, fname)
        with open(dest, "wb") as fh:
            fh.write(base64.b64decode(b64))
        written.append(dest)

    if args.save_kcl and job.get("code"):
        kcl_name = (args.name or "model") + ".kcl"
        kcl_dest = os.path.join(args.output, kcl_name)
        with open(kcl_dest, "w") as fh:
            fh.write(job["code"])
        written.append(kcl_dest)

    print("Wrote:")
    for w in written:
        print(f"  {w}")


if __name__ == "__main__":
    main()
