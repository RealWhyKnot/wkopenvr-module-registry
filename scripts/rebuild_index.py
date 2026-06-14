#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


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


def copy_fields(manifest: dict, fields: tuple[str, ...]) -> dict:
    result = {}
    for field in fields:
        if field in manifest:
            result[field] = manifest[field]
    return result


def main() -> int:
    root = repo_root()
    modules_dir = root / "v1" / "modules"
    modules: list[dict] = []

    for uuid_dir in sorted(p for p in modules_dir.iterdir() if p.is_dir()):
        versions_dir = uuid_dir / "versions"
        versions = sorted(
            (p for p in versions_dir.iterdir() if p.is_dir()),
            key=lambda p: version_key(p.name),
        )
        latest = latest_version(versions, include_prerelease=False)
        manifest = json.loads((latest / "manifest.json").read_text(encoding="utf-8"))

        version_entries: list[dict] = []
        for version_dir in sorted(versions, key=lambda p: version_key(p.name), reverse=True):
            version_manifest = json.loads((version_dir / "manifest.json").read_text(encoding="utf-8"))
            version_entry = copy_fields(
                version_manifest,
                (
                    "version",
                    "sdk_version",
                    "module_api",
                    "payload_url",
                    "payload_sha256",
                    "payload_size",
                    "release_tag",
                    "release_url",
                    "release_channel",
                    "prerelease",
                ),
            )
            version_entries.append(version_entry)

        entry = copy_fields(
            manifest,
            (
                "uuid",
                "name",
                "vendor",
                "description",
                "homepage",
                "version",
                "sdk_version",
                "capabilities",
                "platforms",
                "module_kind",
                "payload_url",
                "payload_sha256",
                "payload_size",
                "release_tag",
                "release_url",
                "release_channel",
                "prerelease",
            ),
        )
        entry["latest"] = manifest["version"]
        entry["versions"] = version_entries
        modules.append(entry)

    index = {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "modules": modules,
    }
    (root / "v1" / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
