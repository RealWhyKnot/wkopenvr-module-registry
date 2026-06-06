#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


REQUIRED_MANIFEST_FIELDS = {
    "schema": int,
    "uuid": str,
    "name": str,
    "vendor": str,
    "version": str,
    "sdk_version": str,
    "min_host_version": str,
    "supported_hmds": list,
    "capabilities": list,
    "platforms": list,
    "module_kind": str,
    "module_api": str,
    "sdk_package": str,
    "entry_assembly": str,
    "entry_type": str,
    "dependencies": list,
    "payload_sha256": str,
    "payload_size": int,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    print(f"::error::{message}", file=sys.stderr)
    sys.exit(1)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON ({exc})")


def version_key(value: str) -> tuple:
    parts = value.split(".")
    if all(part.isdigit() for part in parts):
        return tuple(int(part) for part in parts)
    return (value,)


def validate_manifest(path: Path, expected_uuid: str, expected_version: str) -> dict:
    manifest = read_json(path)

    for field, expected_type in REQUIRED_MANIFEST_FIELDS.items():
        if field not in manifest:
            fail(f"{path}: missing field {field}")
        if not isinstance(manifest[field], expected_type):
            fail(f"{path}: field {field} must be {expected_type.__name__}")

    if manifest["schema"] != 1:
        fail(f"{path}: schema must be 1")
    if manifest["uuid"] != expected_uuid:
        fail(f"{path}: uuid does not match directory name")
    if manifest["version"] != expected_version:
        fail(f"{path}: version does not match directory name")
    if manifest["module_kind"] != "wkopenvr-native":
        fail(f"{path}: module_kind must be wkopenvr-native")
    if manifest["sdk_package"] != "WKOpenVR.FaceTracking.Sdk":
        fail(f"{path}: sdk_package must be WKOpenVR.FaceTracking.Sdk")
    if not manifest["module_api"].startswith("WKOpenVR.FaceTracking.Sdk/"):
        fail(f"{path}: module_api must name the SDK")

    sha = manifest["payload_sha256"]
    if len(sha) != 64 or sha.lower() != sha:
        fail(f"{path}: payload_sha256 must be 64 lowercase hex characters")
    try:
        bytes.fromhex(sha)
    except ValueError:
        fail(f"{path}: payload_sha256 is not valid hex")

    if "windows-x64" not in manifest["platforms"]:
        fail(f"{path}: platforms must include windows-x64")
    if "expression" not in manifest["capabilities"]:
        fail(f"{path}: capabilities must include expression")

    return manifest


def validate_version(version_dir: Path, uuid: str) -> dict:
    manifest_path = version_dir / "manifest.json"
    payload_path = version_dir / "payload.zip"
    if not manifest_path.exists():
        fail(f"{version_dir}: missing manifest.json")
    if not payload_path.exists():
        fail(f"{version_dir}: missing payload.zip")

    manifest = validate_manifest(manifest_path, uuid, version_dir.name)
    payload = payload_path.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != manifest["payload_sha256"]:
        fail(f"{payload_path}: SHA-256 mismatch")
    if len(payload) != manifest["payload_size"]:
        fail(f"{payload_path}: payload_size mismatch")
    return manifest


def validate_index(expected_latest: list[dict]) -> None:
    index_path = repo_root() / "v1" / "index.json"
    if not index_path.exists():
        fail(f"{index_path}: missing")
    index = read_json(index_path)
    if index.get("schema") != 1:
        fail(f"{index_path}: schema must be 1")
    if not isinstance(index.get("modules"), list):
        fail(f"{index_path}: modules must be an array")

    expected_by_uuid = {m["uuid"]: m for m in expected_latest}
    actual_by_uuid = {m.get("uuid"): m for m in index["modules"]}
    if set(expected_by_uuid) != set(actual_by_uuid):
        fail(f"{index_path}: module list does not match v1/modules")

    for uuid, manifest in expected_by_uuid.items():
        entry = actual_by_uuid[uuid]
        for field in ("uuid", "name", "vendor", "version", "capabilities", "platforms", "module_kind", "sdk_version"):
            if entry.get(field) != manifest.get(field):
                fail(f"{index_path}: module {uuid} field {field} is stale")


def main() -> int:
    root = repo_root()
    modules_dir = root / "v1" / "modules"
    if not modules_dir.exists():
        fail(f"{modules_dir}: missing")

    latest_manifests: list[dict] = []
    for uuid_dir in sorted(p for p in modules_dir.iterdir() if p.is_dir()):
        versions_dir = uuid_dir / "versions"
        if not versions_dir.exists():
            fail(f"{uuid_dir}: missing versions directory")

        versions: dict[str, dict] = {}
        for version_dir in sorted(p for p in versions_dir.iterdir() if p.is_dir()):
            versions[version_dir.name] = validate_version(version_dir, uuid_dir.name)

        if not versions:
            fail(f"{uuid_dir}: no versions")

        latest_version = max(versions.keys(), key=version_key)
        latest_manifest = versions[latest_version]
        latest_path = uuid_dir / "manifest.json"
        if not latest_path.exists():
            fail(f"{uuid_dir}: missing latest manifest")
        if read_json(latest_path) != latest_manifest:
            fail(f"{latest_path}: latest manifest does not match latest version")
        latest_manifests.append(latest_manifest)

    validate_index(latest_manifests)
    print("Registry validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
