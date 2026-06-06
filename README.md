# wkopenvr-module-registry

Static native module registry for WKOpenVR face tracking modules.

This registry is separate from `wkvrcft-legacy-registry`. It serves modules built against `WKOpenVR.FaceTracking.Sdk`; legacy VRCFaceTracking packages stay in the legacy registry.

## Endpoints

| URL | Returns |
|---|---|
| `/v1/index` | Latest native module list |
| `/v1/modules/<uuid>/manifest` | Latest module manifest JSON |
| `/v1/modules/<uuid>/versions/<ver>/manifest` | Pinned version manifest |
| `/v1/modules/<uuid>/versions/<ver>/payload` | Module zip |

## Local Validation

```powershell
.\test.ps1
```

The validator checks manifest fields, native metadata, payload SHA-256, latest manifest pointer, and index coherence.

## Publication

No script in this repository publishes to a public host. Publication requires an explicit separate action.
