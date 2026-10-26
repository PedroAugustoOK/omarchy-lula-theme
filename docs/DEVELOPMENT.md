# Development

`colors.toml` is the source of palette values. The installed Omarchy generates
application configurations; this repository's scripts are authoring tools.

## Checks

Python 3.11+ is required; no Python packages are needed.

```bash
python3 scripts/check-theme.py .
python3 -m unittest discover -s tests -v
find scripts -name '*.sh' -print0 | xargs -0 -n 1 bash -n
python3 scripts/check-theme.py . --write-report
```

Commit `docs/PALETTE.md` after palette changes. CI rejects missing keys, invalid
TOML, malformed colors, low contrast, unsupported files, symlinks, broken PNG
chunks and missing assets. Preview dimensions allow normal integer rounding of
16:9, including 1800×1012. Artwork dimensions may differ between themes.

## Asset tooling

Rendering requires Bash, Python 3.11+ and ImageMagick 6 or 7. The shared helper
reads TOML directly, so Omarchy does not have to be installed. `make-preview.sh`,
where present, also requires Fontconfig and a suitable serif font.

Pass a temporary output path when experimenting. Existing wallpapers and static
picker artwork remain checked in; rendering them is not required for installation.
Do not use an abstract composition as evidence of a working desktop capture.

## Manual verification on Omarchy

Before a release, install the branch on an Omarchy machine, switch themes and
inspect shell menus, notifications, lock input, terminals and available editors.
Check selected text, comments, diagnostics and both normal and intense ANSI
colors. Capture the real desktop for the README. The automated audit cannot
exercise that session; no live desktop validation is claimed by this update.

## Publication

Use the repository description and topics for discoverability. Suggested topics:
`omarchy-theme`, `dark`, `red`, `minimal`, `warm`.

The [theme registry](https://github.com/omacom/omarchy-theme-registry) documents
submission and current catalog validation. Local checks complement that service;
they do not claim to reproduce its complete rules. Submit only after manual QA.
