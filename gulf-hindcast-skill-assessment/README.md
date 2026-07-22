# Gulf Hindcast Skill Assessment

Source for *Regional Ocean Modelling in the Arabian Gulf — Wave and Circulation Hindcast Skill Assessment* (Asset 1 of the Ocean Motion Analytics publication series).

## Layout

```
v1.0-plan.md                 -- locked scope and execution plan for v1.0
_quarto.yml                  -- Quarto book project configuration
index.qmd                    -- Preface
01-introduction.qmd          -- Ch. 1
02-model-setup-methodology.qmd
03-temperature-salinity.qmd
04-water-level.qmd
05-waves.qmd
06-limitations-roadmap.qmd
changelog.qmd                -- Back matter
references.qmd               -- Auto-generated from refs.bib
refs.bib                     -- Bibliography (seed)
style/
  in-header.tex              -- Sober report typography (KOMA-Script)
  before-body.tex            -- Custom title page
figures/                     -- Figures used in chapters
```

## Build

From this directory:

```
quarto render                # render to PDF (output in _book/)
quarto preview               # live preview while editing
```

You'll need Quarto and a TeX engine. If you don't have one:

```
quarto install tinytex
```

## Versioning

The version on the cover and in the changelog is `v1.0`, set in `_quarto.yml` under `metadata.version` and in `style/before-body.tex`. Bump both, update `changelog.qmd`, and tag the commit (e.g. `gulf-hindcast/v1.1`) on release.

## Figure sources

Figures live in `figures/` and are copied or symlinked from generated outputs in `~/code/oceanmotion-models/configs/gulf_01/...`. Quarto's `freeze: auto` is enabled so that figure regeneration is decoupled from the prose-edit cycle.
