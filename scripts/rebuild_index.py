#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def version_key(value: str) -> tuple:
    parts = value.split(".")
    if all(part.isdigit() for part in parts):
        return tuple(int(part) for part in parts)
    return (value,)


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
        latest = versions[-1]
        manifest = json.loads((latest / "manifest.json").read_text(encoding="utf-8"))
        modules.append(
            {
                "uuid": manifest["uuid"],
                "name": manifest["name"],
                "vendor": manifest["vendor"],
                "version": manifest["version"],
                "capabilities": manifest["capabilities"],
                "platforms": manifest["platforms"],
                "module_kind": manifest.get("module_kind", "wkopenvr-native"),
                "sdk_version": manifest["sdk_version"],
            }
        )

    index = {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "modules": modules,
    }
    (root / "v1" / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
