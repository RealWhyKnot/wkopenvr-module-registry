#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_UUID = "4df7850f-1d75-4665-9eab-6f07e0f3b5dc"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wkopenvr-registry-import-") as temp:
        work = Path(temp) / "registry"
        shutil.copytree(ROOT / "scripts", work / "scripts")
        shutil.copytree(ROOT / "v1", work / "v1")

        package = Path(temp) / "WKOpenVR.SyntheticFaceModule.2026.6.9.0-beta.zip"
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", "{}")
            archive.writestr("assemblies/WKOpenVR.SyntheticFaceModule.dll", "test")

        manifest = {
            "schema": 1,
            "uuid": SYNTHETIC_UUID,
            "name": "WKOpenVR Synthetic Face Module",
            "vendor": "WhyKnot",
            "homepage": "https://github.com/RealWhyKnot/WKOpenVR.SyntheticFaceModule",
            "license": "GPL-3.0-only",
            "version": "2026.6.9.0-beta",
            "sdk_version": "2026.6.9.0-beta",
            "min_host_version": "1.0",
            "supported_hmds": ["*"],
            "capabilities": ["expression", "audio", "eye"],
            "platforms": ["windows-x64"],
            "module_kind": "wkopenvr-native",
            "module_api": "WKOpenVR.FaceTracking.Sdk/2026.6.9.0-beta",
            "sdk_package": "WKOpenVR.FaceTracking.Sdk",
            "entry_assembly": "WKOpenVR.SyntheticFaceModule.dll",
            "entry_type": "WKOpenVR.SyntheticFaceModule.SyntheticFaceModule",
            "dependencies": [],
            "release_tag": "v2026.6.9.0-beta",
            "release_url": "https://github.com/RealWhyKnot/WKOpenVR.SyntheticFaceModule/releases/tag/v2026.6.9.0-beta",
            "release_channel": "stable",
            "prerelease": False,
            "payload_url": "https://github.com/RealWhyKnot/WKOpenVR.SyntheticFaceModule/releases/download/v2026.6.9.0-beta/WKOpenVR.SyntheticFaceModule.2026.6.9.0-beta.zip",
            "payload_sha256": "0" * 64,
            "payload_size": 0,
        }
        manifest_path = Path(temp) / "WKOpenVR.SyntheticFaceModule.2026.6.9.0-beta.manifest.json"
        write_json(manifest_path, manifest)

        result = subprocess.run(
            [
                sys.executable,
                str(work / "scripts" / "import_synthetic_release.py"),
                "--registry-root",
                str(work),
                "--payload",
                str(package),
                "--manifest",
                str(manifest_path),
                "--beta",
            ],
            cwd=work,
        )
        if result.returncode != 0:
            return result.returncode

        imported_manifest = json.loads(
            (work / "v1" / "modules" / SYNTHETIC_UUID / "versions" / "2026.6.9.0-beta" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        expected_url = (
            "https://wkopenvr-module-registry.whyknot.dev/v1/modules/"
            f"{SYNTHETIC_UUID}/versions/2026.6.9.0-beta/payload"
        )
        if imported_manifest["payload_url"] != expected_url:
            raise AssertionError("Importer did not rewrite payload_url to the registry URL.")
        if imported_manifest["release_channel"] != "beta" or imported_manifest["prerelease"] is not True:
            raise AssertionError("Importer did not force beta prerelease metadata.")

        index = json.loads((work / "v1" / "index.json").read_text(encoding="utf-8"))
        version_entry = index["modules"][0]["versions"][0]
        if version_entry["version"] != "2026.6.9.0-beta":
            raise AssertionError("Imported version was not added to the rebuilt index.")
        if version_entry["release_channel"] != "beta" or version_entry["prerelease"] is not True:
            raise AssertionError("Imported beta metadata was not added to the rebuilt index.")

    print("Synthetic release import tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
