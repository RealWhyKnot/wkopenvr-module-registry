#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


REGISTRY_BASE_URL = "https://wkopenvr-module-registry.whyknot.dev"
SYNTHETIC_UUID = "4df7850f-1d75-4665-9eab-6f07e0f3b5dc"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    print(f"::error::{message}", file=sys.stderr)
    raise SystemExit(1)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"{path}: missing")
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON ({exc})")


def version_key(value: str) -> tuple:
    numeric, separator, suffix = value.partition("-")
    parts = numeric.split(".")
    if all(part.isdigit() for part in parts):
        return (tuple(int(part) for part in parts), 0 if separator else 1, suffix)
    return ((-1,), 0, value)


def is_prerelease(value: str) -> bool:
    return "-" in value


def latest_version(versions: list[Path], include_prerelease: bool = False) -> Path:
    candidates = [v for v in versions if include_prerelease or not is_prerelease(v.name)]
    if not candidates:
        candidates = versions
    return max(candidates, key=lambda p: version_key(p.name))


def require_string(manifest: dict, field: str) -> str:
    value = manifest.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f"Manifest field {field} must be a non-empty string.")
    return value.strip()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_script(root: Path, name: str) -> None:
    script = root / "scripts" / name
    result = subprocess.run([sys.executable, str(script)], cwd=root)
    if result.returncode != 0:
        fail(f"{script} failed with exit code {result.returncode}")


def import_release(registry_root: Path, payload_path: Path, manifest_path: Path, beta: bool) -> None:
    payload_path = payload_path.resolve()
    manifest_path = manifest_path.resolve()
    if not payload_path.exists():
        fail(f"{payload_path}: missing")
    if not manifest_path.exists():
        fail(f"{manifest_path}: missing")

    manifest = read_json(manifest_path)
    uuid = require_string(manifest, "uuid")
    version = require_string(manifest, "version")
    if uuid != SYNTHETIC_UUID:
        fail(f"Unexpected synthetic module uuid: {uuid}")
    if beta and not version.endswith("-beta"):
        fail("Beta registry imports must use a version ending in -beta.")

    manifest["release_channel"] = "beta" if beta else ("beta" if is_prerelease(version) else "stable")
    manifest["prerelease"] = beta or is_prerelease(version)
    manifest["payload_url"] = f"{REGISTRY_BASE_URL}/v1/modules/{uuid}/versions/{version}/payload"
    manifest["payload_sha256"] = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    manifest["payload_size"] = payload_path.stat().st_size

    version_dir = registry_root / "v1" / "modules" / uuid / "versions" / version
    version_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(payload_path, version_dir / "payload.zip")
    write_json(version_dir / "manifest.json", manifest)

    module_dir = registry_root / "v1" / "modules" / uuid
    versions_dir = module_dir / "versions"
    versions = sorted((p for p in versions_dir.iterdir() if p.is_dir()), key=lambda p: version_key(p.name))
    latest = latest_version(versions, include_prerelease=False)
    latest_manifest = read_json(latest / "manifest.json")
    write_json(module_dir / "manifest.json", latest_manifest)

    run_script(registry_root, "rebuild_index.py")
    run_script(registry_root, "validate.py")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-root", default=str(repo_root()))
    parser.add_argument("--payload", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--beta", action="store_true")
    args = parser.parse_args()

    import_release(
        Path(args.registry_root).resolve(),
        Path(args.payload),
        Path(args.manifest),
        args.beta,
    )
    print("Synthetic module release imported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
