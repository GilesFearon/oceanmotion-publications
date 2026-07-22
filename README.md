# oceanmotion-publications

Source for Ocean Motion Analytics public publications. Each top-level directory is one publication asset.

## Assets

| Dir | Asset |
|---|---|
| `gulf-hindcast-skill-assessment/` | Asset 1 — *Regional Ocean Modelling in the Arabian Gulf — Wave and Circulation Hindcast Skill Assessment* |
| (planned) `gulf-coastal-turbidity/` | Asset 2 — *Coastal Turbidity Modelling in the Arabian Gulf — Hindcast Climatology and Skill Assessment* |
| (planned) `capability-statement/` | Asset 3 — Capability one-pager |

## Build

Each asset is a Quarto project. From the asset directory:

```
quarto render        # build PDF (and HTML if configured)
quarto preview       # live preview
```

Requires Quarto and a TeX engine. Recommended:

```
# Quarto: https://quarto.org/docs/get-started/
# TeX (Quarto's TinyTeX is sufficient):
quarto install tinytex
```

## Versioning

Each asset is a single Quarto project that gets re-rendered as evidence accumulates. Versions are git tags (e.g. `gulf-hindcast/v1.0`). The version number appears on the cover and in the back-matter changelog.
