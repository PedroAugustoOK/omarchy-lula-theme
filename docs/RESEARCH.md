# Lula — Omarchy Theme Research

**Date:** 2026-10-21 (latest audit)
**Omarchy version tested:** 4.0.4-1 (2026-10-16), re-audited on 4.0.5-1 (2026-10-17) and on **4.0.6-1** (2026-10-21); `version` file reports `4.0.0.alpha`
**Machine:** Arch Linux, current theme at first research time: `Ankh Dark`

This document records how the Omarchy theme system actually works on the
installed version, verified against source files and local installation —
not from memory or old tutorials.

## Sources consulted

1. `https://omarchy.org/manual/making-your-own-theme/` — official manual
   (Making your own theme). Confirms `~/.config/omarchy/themes`, `colors.toml`
   as main file, `mode = "light"`, `icons.theme` Yaru options, `unlock.png` /
   `preview-unlock.png` + `omarchy plymouth preview`, template dir
   `~/.config/omarchy/themed/*.tpl`, repo naming `omarchy-[name]-theme`.
2. `https://omarchythemes.dev/docs/create` — Seven steps, minimal repo
   (colors.toml + backgrounds + README + LICENSE), directory-name stripping
   rules.
3. `https://omarchythemes.dev/docs/anatomy` — Full file tree, file reference,
   installed-theme limits (no `*.lua`, no terminal configs, no `vscode.json`,
   no symlinks), `shell.toml` vs `shell.<section>.toml`, hand-written app
   colours list.
4. `https://omarchythemes.dev/docs/colors` — Complete palette shape (26 keys,
   no tables), key roles, mode resolution order, derived values table, legacy
   `bg`/`colorN`/`purple` aliases, `{{ key }}` / `{{ key_strip }}` /
   `{{ key_rgb }}` / `mix` / `hypr_gradient` / `shell_gradient` /
   `gradient_start` placeholders.
5. `https://omarchythemes.dev/docs/palettes` — Contrast targets
   (fg/bg 7:1 ideal, 4.5 floor; secondary ≥4.5; accent/bg ≥3:1; ANSI/bg ≥4.5;
   selection pairing ≥4.5), neutral ramp order, ANSI semantics, one-accent rule.
6. `https://omarchythemes.dev/docs/backgrounds` — `backgrounds/` flat
   (1 level, jpg/jpeg/png/gif/bmp/webp, sorted, `Super+Ctrl+Space` cycles,
   `~/.local/state/omarchy/current/background` symlink), ≥2560×1440
   (prefer 3840×2160), JPEG photo / PNG graphic, <3 MB each, licensing +
   attribution required.
7. `https://omarchythemes.dev/docs/publishing` — `omarchy-<name>-theme`
   convention, `omarchy theme install <url>` clones to
   `~/.config/omarchy/themes/<name>` and applies immediately, name validation
   `^[a-z0-9_][a-z0-9._+-]*$` (lowercased), pre-publish checklist.
8. Local skill: `/usr/share/omarchy/default/agents/skills/omarchy/theming.md`
   — New-theme recipe, overlay vs fork for stock themes, font commands.
9. Local code (authoritative):
   - `/usr/share/omarchy/bin/omarchy-theme-set` (staging, deny list, overlay,
     background cycling, post hooks)
   - `/usr/share/omarchy/bin/omarchy-theme-install` (URL check, name
     derivation, clone, apply)
   - `/usr/share/omarchy/bin/omarchy-theme-set-templates` (sed-based
     `{{ }}` expansion, user tpl overrides built-in, `shell.<section>.toml`
     merging)
   - `/usr/share/omarchy/bin/omarchy-theme-color` (canonical parser, alias
     cascade, derivations, mode resolution — shared by all consumers)
   - `/usr/share/omarchy/default/themed/*.tpl` (19 templates on 4.0.6-1)
   - `/usr/share/omarchy/themes/*/colors.toml`, `icons.theme`, `vscode.json`,
     `neovim.lua`, `keyboard.rgb`, `shell.lock.toml`
   - `~/.config/omarchy/themes/ankh-dark/` (user theme example with
     `btop.theme`, `helix.toml`, `shell.toml`, `vscode-theme.json`,
     `theme.toml`)
10. Live commands: `omarchy theme list/current/dir`, `omarchy dev theme-preview`.

`https://github.com/omacom/omarchy/blob/quattro/docs/theming.md` and
`https://omarchy.org/themes/` were referenced by the brief; the manual +
local skill + installed scripts supersede them on this version and were
verified directly. The repo path `omacom/omarchy` in the brief is stale —
the installed package cites `https://github.com/basecamp/omarchy`.

## 1. How Omarchy identifies, installs, loads and switches themes

- **Stock themes:** `/usr/share/omarchy/themes/<slug>/` (e.g. `tokyo-night`,
  `catppuccin`, `matte-black`). Lowercase slugs with dashes.
- **User themes:** `~/.config/omarchy/themes/<slug>/`. `omarchy theme list`
  merges both; user dir overlays stock of the same slug.
- **Name normalisation:** `omarchy-theme-set` lowercases, strips `<...>`,
  spaces → dashes. `tokyo-night` and `Tokyo Night` both work.
- **Install:** `omarchy theme install <git-url>` → `omarchy-git-url-check`
  (rejects transport helpers) → derives slug from basename:
  strip `.git`, strip leading `omarchy-`, strip trailing `-theme`,
  lowercase → validate `^[a-z0-9_][a-z0-9._+-]*$` → `rm -rf` existing →
  `git clone <url> ~/.config/omarchy/themes/<slug>` → `omarchy-theme-set`.
  SSH URLs also work. Menu path: `Install > Style > Theme`.
- **Set (`omarchy-theme-set`):**
  1. `flock` on `${XDG_RUNTIME_DIR:-/tmp}/omarchy-theme-set.lock`.
  2. `rm -rf next-theme; mkdir next-theme`; copy stock theme first, then
     overlay user theme on top (overlay model).
  3. If user theme has `.git` (and is not a symlink) → **installed-from-repo
     mode**: copy file-by-file, **dropping** denied files, never following
     symlinks; else copy everything.
  4. If no `colors.toml` but `alacritty.toml` exists → derive palette via
     `omarchy-theme-colors-from-alacritty` (legacy support).
  5. `omarchy-theme-set-templates`: expand every `*.tpl`
     (user `~/.config/omarchy/themed/` first, then built-in
     `$OMARCHY_PATH/default/themed/`) with resolved palette; skip outputs
     the theme already ships hand-written; then merge `shell.<section>.toml`.
  6. Atomic swap `next-theme → ~/.local/state/omarchy/current/theme`,
     write `theme.name`, push palette to running shell via
     `omarchy-shell ... applyTheme`, transition background
     (`current/background` symlink, `Super+Ctrl+Space` cycles sorted list
     from `~/.config/omarchy/backgrounds/<theme>/` + theme `backgrounds/`),
     then parallel post-hooks: restart terminal/hyprctl/btop/opencode/helix,
     `theme-set-foot/tmux/gnome/pi/claude/hermes/t3code/browser/vscode/
     obsidian/keyboard`, `omarchy-hook theme-set`, warm switcher caches.
- **Extras/update/remove:** `theme extras` lists `~/.config/omarchy/themes/*`
  with `.git` (non-symlink); `theme update` pulls them; `theme remove`
  deletes user theme; `theme refresh` regenerates from templates;
  `theme bg next/set/current/cache` manage wallpapers.
- **Headless:** `OMARCHY_THEME_HEADLESS=1` / `OMARCHY_THEME_OFFLINE=1` and
  `OMARCHY_THEME_SKIP_BACKGROUND=1` supported (ISO builds).

## 2. Installed version and supported features

- Package `omarchy 4.0.6-1` (first audited on 4.0.4-1), shell = Quickshell
  (`omarchy-shell`), compositor Hyprland, 19 built-in templates (see §4),
  `gum` menus, Plymouth/SDDM integration (`omarchy plymouth preview/set`,
  `unlock.png`), RGB keyboard hook, GNOME key, VS Code extension auto-install,
  Chromium/Obsidian/Claude/Pi/Hermes/T3Code/Zed theming hooks.
- `omarchy dev theme-preview [name|dir|colors.toml]` renders ramp,
  contrast (`foreground/background`), selection sample, ANSI strips.
- `omarchy-theme-color --file <colors.toml> --all|--raw|<key> [fallback]`
  is the single shared resolver — templates, OSC, tmux, GNOME and previews
  all agree through it.

## 3. `colors.toml` — complete reference (verified)

Flat TOML, no tables. Canonical 26 keys (every stock theme uses these):

```toml
mode = "dark"            # "dark" | "light" — explicit; see mode order below

accent = "#..."          # remembered-by colour: focused borders, active bar,
                         # links, selected rows. Falls back to color4 in some
                         # surfaces. Usually equals one ANSI (often blue).
selection = "#..."       # selected-text background; derives
                         # selection_background; paired with bright_foreground
muted = "#..."           # de-emphasis: comments, placeholders, dividers;
                         # also ANSI color8

background = "#..."       # primary surface; ANSI color0
dark_background = "#..."  # recessed (explicit; auto = bg 25%→black — wrong
darker_background = "#..."#   for light themes, so write them)
lighter_background = "#..." # raised: cards, popovers, hovered row; must not
                         # collide with selection

foreground = "#..."       # primary text; ANSI color7
dark_foreground = "#..."  # secondary text (≥4.5:1 vs bg)
light_foreground = "#..." # emphasised text (fallback color7)
bright_foreground = "#..."# brightest; ANSI color15; terminal/editor cursor;
                         # selection_foreground defaults to this

red = "#..."             # error + shell urgent role (no `urgent` key — ignored)
yellow = "#..."          # warning
orange = "#..."          # defaults to yellow if absent
green = "#..."           # success
cyan = "#..."
blue = "#..."
magenta = "#..."         # `purple` accepted as synonym
brown = "#..."           # defaults to orange 50%→black if absent

bright_red = "#..."      # each defaults to base 20%→white if absent
bright_yellow = "#..."
bright_green = "#..."
bright_cyan = "#..."
bright_blue = "#..."
bright_magenta = "#..."
```

Optional gradient keys (used by Hyprland + shell templates):

```toml
hyprland_active_border = "rgba(E63950ee) rgba(761C30ee) 45deg"
hyprland_inactive_border = "rgba(4a1e2aaa)"
```

Consumed via `{{ hypr_gradient hyprland_active_border accent }}` and
`{{ shell_gradient hyprland_active_border accent }}` with fallback to
`accent`. Seen in `hackerman`, `last-horizon`, `solitude`, `lumon`.
`active_border_color` / `active_tab_background` appear in some stock themes
but no current template reads them (kitty template hardcodes `accent`) —
omitted from Lula as dead keys.

**Mode resolution order:** `mode` → legacy `theme_type` → `light.mode` file
→ background luminance (ΣRGB > 382 = light) → dark. Always set `mode`.

**Derivations (floors, not taste):** bg/fg ← color0/color7;
light_fg ← color7/fg; bright_fg ← color15/fg; lighter_bg ← color0/bg;
dark_fg ← color8/fg; muted ← color8/dark_fg; selection ←
selection_background/color8/color0/bg; selection_background ← selection;
selection_foreground ← bright_fg; cursor ← bright_fg; orange ← yellow;
brown ← orange 50%→black; dark_bg ← bg 25%→black; darker_bg ← bg 50%→black;
bright_* ← base 20%→white. Legacy aliases both ways: `bg/dark_bg/darker_bg/
lighter_bg/fg/dark_fg/light_fg/bright_fg`, `color0..color15`, `purple`.

**Template placeholders:** `{{ key }}` → `#rrggbb`; `{{ key_strip }}` →
`rrggbb`; `{{ key_rgb }}` → `R,G,B`; `{{ mix a b 15% }}` (+`_strip`/`_rgb`);
`{{ hypr_gradient key fallback }}` / `{{ shell_gradient … }}` /
`{{ gradient_start … }}` for gradient keys. Only `[a-zA-Z0-9_-]` keys and
`[#(),._+/% -]` values accepted, else warned + skipped.

## 4. Templates and auto-generation

`omarchy-theme-set-templates` builds a sed script from
`omarchy-theme-color --all` and expands every template whose output the
theme does **not** already ship. User `~/.config/omarchy/themed/*.tpl`
wins over built-in. Built-ins (20):

`alacritty.toml`, `btop.theme`, `chromium.theme` (single `R,G,B` line!),
`claude.json`, `foot.ini`, `ghostty.conf`, `gum_env.lua`, `helix.toml`,
`hermes.yaml`, `hyprland-preview-share-picker.css`, `hyprland.lua`,
`keyboard.rgb`, `kitty.conf`, `neovim.lua` (aether.nvim + LazyVim),
`obsidian.css`, `pi.json`, `shell.toml` (sections: bar, hyprland, controls,
spacing, font, popups, tooltip, notifications, launcher, menu, polkit, lock,
image-picker), `t3code.json`, `vscode-theme.json` (+`theme_type`).

Hand-written theme files suppress generation for that output only.
`shell.<section>.toml` (e.g. `shell.lock.toml`, `shell.bar.toml`) patches
one `[section]` after generation; full `shell.toml` replaces everything.
`alacritty.toml.tpl.sample` in `~/.config/omarchy/themed/` documents all
variables.

**Rule applied to Lula:** ship no generated-equivalent files; rely on
`colors.toml` so every app stays in sync. Only `colors.toml`,
`backgrounds/`, `icons.theme`, `keyboard.rgb`, `preview.png`,
`unlock.png` + `preview-unlock.png`, docs.

## 5. Required / optional / incompatible files for GitHub themes

- **Required:** `colors.toml` in repo root (gallery importer reads it as
  data; legacy `alacritty.toml`-only themes are converted in scratch).
- **Recommended:** `backgrounds/` (≥1 wallpaper), `preview.png` (1800×1012
  like stock), `README.md` (screenshot, purpose, background credits),
  `LICENSE` (MIT default; note if backgrounds differ).
- **Optional but kept:** `icons.theme`, `keyboard.rgb`, `btop.theme`,
  `chromium.theme`, `helix.toml`, `hermes.yaml`, `obsidian.css`,
  `claude.json`, `pi.json`, `t3code.json`, `vscode-theme.json`,
  `shell.toml`, `shell.<section>.toml`, `backgrounds/`, `preview.png`,
  `unlock.png` + `preview-unlock.png`, `light.mode` (legacy),
  `README.md`, `LICENSE`, `*.md`, `*.txt`.
- **Dropped when cloned (regenerated, named on stderr):**
  `INSTALLED_THEME_DENIED = (alacritty.toml foot.ini ghostty.conf
  kitty.conf vscode.json)` **plus any `*.lua`** (`hyprland.lua`,
  `gum_env.lua`, `neovim.lua`, …) **plus every symlink at any depth**.
  Rationale: compositor Lua runs at login, terminal configs name the
  launched program, `vscode.json` installs arbitrary-JS extensions.
  `.git` presence = stranger; symlink theme = working copy (unrestricted);
  hand-written `~/.config/omarchy/themes/*` without `.git` = unrestricted.
- **Never ship** `.lua`, terminal configs, `vscode.json` as the theme's
  mechanism — the theme must look right from `colors.toml` alone.

## 6. Integration with components

| Component | Mechanism |
|---|---|
| Hyprland (borders, groups) | `hyprland.lua` generated from `accent` / `hyprland_*_border` |
| Top bar + shell (bar, menus, launcher, popups, tooltip, notifications, OSD, lock, image-picker) | `shell.toml` generated; bar `active = red`, lock `border = hyprland.active-border`, `border-error = red`, `selection = accent` |
| Menus / launcher (gum) | `gum_env.lua` from selection/fg/bg/accent/muted |
| Notifications | shell `[notifications]` + `omarchy-notification-send` |
| Lock screen | shell `[lock]` + `unlock.png`/`preview-unlock.png` → `Style > Unlock`; Plymouth via `omarchy plymouth preview/set` |
| Terminals (Alacritty/Foot/Ghostty/Kitty) | generated configs from 16 ANSI + cursor/selection; live-restarted on set |
| Neovim | generated `neovim.lua` (aether.nvim palette = full `colors.toml`); stock themes additionally ship a hand `neovim.lua` pinning e.g. `tokyonight.nvim` — dropped on clone, so Lula relies on aether |
| VS Code | generated `vscode-theme.json` (Omarchy theme); stock `vscode.json` (extension pointer) dropped on clone |
| Chromium | `chromium.theme` = `background_rgb` + hooks `theme-set-browser*` |
| btop | `btop.theme` generated (proc/cpu/mem/net boxes map to accent/magenta/green/red…); restarted on set |
| Helix / Obsidian / Claude / Pi / Hermes / T3Code / Zed / tmux / GNOME / Emacs | generated `helix.toml` etc. + `theme-set-*` hooks |
| Icons | `icons.theme` single line, Yaru family (`Yaru`, `Yaru-blue`, `Yaru-dark`, `Yaru-magenta`, `Yaru-olive`, `Yaru-prussiangreen`, `Yaru-purple`, `Yaru-red`, `Yaru-sage`, `Yaru-wartybrown`, `Yaru-yellow`); Lula → `Yaru-red` (as `matte-black` does) |
| Keyboard RGB | `keyboard.rgb` six hex, no `#` (e.g. `e63950`); generated from `{{ accent_strip }}`-equivalent if absent |
| Screensaver/branding | `omarchy branding screensaver/about`, not per-theme |

## 7. Wallpapers, previews, icons, colours

- `backgrounds/` flat, sorted; user extras in
  `~/.config/omarchy/backgrounds/<slug>/`; `preview.png` = picker
  thumbnail (stock 1800×1012 PNG); `unlock.png` transparent PNG
  (stock 800×188–1108×523) + `preview-unlock.png` (1920×1080) → listed in
  `Style > Unlock`, preview via `omarchy plymouth preview <bg-hex>
  <text-hex> <logo> <out>`; `icons.theme` → file-manager set;
  `keyboard.rgb` → ASUS/F16 hooks; colours → everything via §4.

## 8. Installing from a Git repo

`omarchy theme install https://github.com/USER/omarchy-lula-theme.git`
(validated URL, slug `lula`, clone, apply). Pre-publish: README +
screenshot + credits, LICENSE, `preview.png`, no Lua/terminal/vscode.json
dependence, **real install test from URL on a clean machine**.

## 9. Best practices observed (stock + community)

Minimal publishable repo = `colors.toml + backgrounds/ + README + LICENSE`
(+ `preview.png`, `icons.theme`, `keyboard.rgb`); numbered wallpaper
prefixes (`001-…`); ≤3 MB/file; JPEG photo / PNG graphic; no SVG; no
copyrighted images without redistribution licence + `CREDITS`; one accent
(usually an ANSI); tinted neutrals; even 7-step ramp
`darker_bg→…→lighter_bg / dark_fg→…→bright_fg`; `lighter_bg ≠ selection`;
real `dark_bg` distance; red/green lightness-separated (colour-blind);
bright_* visibly brighter; light themes darken ANSI + avoid pure white.

## 10. Version differences affecting compatibility

- `mode` key supersedes `light.mode` file (both honoured; set `mode`).
- `colors.toml` supersedes legacy `alacritty.toml`-only themes (auto-converted).
- `shell.<section>.toml` partial overrides are current; full `shell.toml`
  still replaces all.
- Deny list is exactly `*.lua + 4 terminal configs + vscode.json +
  symlinks` — `btop.theme`/`chromium.theme`/`helix.toml`/`icons.theme`/
  `keyboard.rgb`/`shell.toml` are **kept**, contrary to some old guides
  that claim terminal configs ship.
- `omarchy theme install` name rules + URL check are enforced (spaces,
  quotes, non-ASCII refused); `omarchy-…-theme` stripping is the only
  naming magic.
- Package `4.0.4-1` vs `version` file `4.0.0.alpha`: behaviour above is
  from the installed scripts, which are authoritative for this machine.

## 11. Post-update audit on Omarchy 4.0.5-1 (2026-10-17)

Re-audit after the system update. All Lula checks pass unchanged; the
mechanism documented above is still current. Differences observed 4.0.4 → 4.0.5:

- **New hard dependency `omarchy-themes-intros`** ("Background intro videos
  for the Omarchy themes"): ships `backgrounds/intros/*.mp4` (192–752 KB
  each) for the *official* themes only. Stock Omarchy has **no consumer** for
  these files: nothing in `/usr/share/omarchy` (`bin/`, `shell/` QML,
  `default/themed/`) references `intros` or plays theme-side mp4s. They are
  assets for the optional wallpaper engine **OWE** (`omacom/owe`, `omarchy
  pkg add owe`), which plays per-file intros via `owe intro` / a login handoff
  and watches the `~/.local/state/omarchy/current/background` symlink + an
  optional `omarchy hook install theme-set /usr/share/owe/10-owe-sync`. A
  git-installed theme may ship a small intro (it would be staged into
  `backgrounds/intros/` and inert without OWE — `choose_theme_background`
  matches only images at depth 1, so mp4s never join the rotation).
- **Theme switching gained crossfade**: `omarchy-theme-set` snapshots the
  outgoing background and calls `shell_ipc background themeTransition …`
  before rotating `~/.local/state/omarchy/current/background`. Also warm
  selector caches (`omarchy-theme-switcher --preload`, `omarchy theme bg
  cache` thumbnails).
- **Staging pipeline same contract**: deny list for git themes unchanged
  (`*.lua` + `alacritty.toml foot.ini ghostty.conf kitty.conf vscode.json`
  + symlinks + optional `colors.toml` derived from `alacritty.toml`). Docs
  (`*.md`, `LICENSE`) are staged but exempt from "ignored" reporting.
  Theme slug is written to `~/.local/state/omarchy/current/theme.name`
  (lowercase); `omarchy theme current` prettifies it ("Lula").
- **New theme set hooks** beyond the known ones: `omarchy-theme-set-tmux`,
  `-gnome`, `-pi`, `-claude`, `-hermes`, `-t3code`, `-obsidian` — all
  generated from `colors.toml` resolutions; a colors.toml theme contributes
  nothing itself. New template placeholders in the built-in set resolved
  fine: `{{ purple }}` (magenta alias), `{{ mode }}` / `{{ theme_type }}`,
  `*_strip` variants, `background_rgb`, `{{ mix a b 6–52% }}`,
  `{{ hypr_gradient hyprland_active_border accent }}`,
  `{{ hyprland_inactive_border … }}`. `omarchy-theme-color --all` resolves
  71 keys with zero unresolved placeholders; staged configs are
  **byte-identical** to the 4.0.4 output.
- **New CLI surface**: `omarchy theme refresh` (re-stage current theme from
  templates, `OMARCHY_THEME_SKIP_BACKGROUND=1` — the post-update command),
  `omarchy theme update` (git pull every theme cloned under
  `~/.config/omarchy/themes`), `omarchy theme extras` (lists git-installed
  themes), `omarchy theme bg cache`, `omarchy-plymouth-set-by-theme
  <theme>` (sudo; applies `colors.toml background/foreground` +
  `unlock.png` as the boot screen — not run automatically).
- **`omarchy-plymouth-preview` "hang" explained**: the script ends with
  `imv -f "$output_path"` — it opens the rendered PNG in a viewer and
  blocks until the window closes. File is written before `imv`; no upstream
  bug report needed. Run with a short timeout or close the viewer.
- **e2e re-verification on 4.0.5**: `omarchy theme install
  https://github.com/PedroAugustoOK/omarchy-lula-theme` → EXIT 0, clone
  under `~/.config/omarchy/themes/lula`, no "Ignored in …" warnings;
  `omarchy theme set lula` (skip-background) → EXIT 0; staged tree
  identical to snapshot; zero `{{ }}` leftovers in staged configs;
  `omarchy theme list` shows "Lula"; switcher preview resolves via
  `preview.png`.

## 12. Post-update audit on Omarchy 4.0.6-1 (2026-10-21)

Re-audit after the system update. The mechanism documented above is still
current — the staging flow, the deny list, the resolver cascade and the
`hypr_gradient` / `shell_gradient` expansion are byte-for-byte the same
behaviour as on 4.0.5. What this audit added:

- **Template count is 19, not 20.** `/usr/share/omarchy/default/themed/` on
  4.0.6-1 holds exactly 19 `*.tpl`: `alacritty, btop, chromium, claude,
  foot, ghostty, gum_env, helix, hermes, hyprland,
  hyprland-preview-share-picker, keyboard.rgb, kitty, neovim, obsidian, pi,
  shell, t3code, vscode-theme`. The `fcitx5-theme.conf.tpl` template named in
  the upstream docs does **not** exist in this package (there is no
  `omarchy-theme-set-fcitx5` binary either), so it was never part of the
  20 counted before — §2 and the source list now say 19.
- **A symlinked theme is treated as user-written and staged in full.**
  `omarchy-theme-set` decides with
  `theme_came_from_a_repo() { [[ ! -L $source && -d $source/.git ]]; }` — a
  symlink short-circuits the filter, so a theme directory that is a symlink
  to a working copy stages `.lua`, terminal configs and `vscode.json` like a
  hand-written theme. This is the supported way to develop a theme locally
  against `~/.config/omarchy/themes/<slug>`.
  Trade-off: `omarchy-theme-extras` skips symlinks, so `omarchy theme update`
  no longer `git pull`s them — pull the working copy by hand instead.
- **`omarchy-theme-set` serializes on a `flock`** and releases the lock
  before the slow app-retint group, so two concurrent `omarchy theme set`
  calls queue instead of racing over the shared `next-theme` staging
  directory. `OMARCHY_THEME_WAIT=1` makes the command wait for every retint
  (needed under systemd, where the oneshot unit's cgroup would otherwise
  kill the background group).
- **`omarchy dev theme-preview` gained a "Neutral ramp" section** listing
  the resolved surfaces and foregrounds ordered by luminance. It is the
  cheapest way to see a ramp inversion: on this audit Lula printed
  `light_foreground` *above* `bright_foreground`, i.e. the cursor / ANSI 15
  color was not the top of the neutral ramp. Fixed by swapping the two
  values (`light_foreground #F5E9EC`, `bright_foreground #FBEFF3`); the
  official tool now prints a strictly monotonic ramp.
- **`omarchy-restart-opencode` is in the post-theme retint list**, so an
  OpenCode session picks up the new palette on a theme switch.
- **e2e re-verification on 4.0.6**: staged tree from `omarchy theme set lula`
  contains zero `{{ }}` leftovers in any generated config; every generated
  JSON (`vscode-theme`, `claude`, `pi`, `t3code`, `spotifast`, `zapfast`)
  parses; `hyprland.lua` renders the border as
  `{ colors = { "rgba(E63950ee)", "rgba(761C30ee)" }, angle = 45 }` and
  `shell.toml [hyprland]` as
  `rgba(E63950ee) rgba(761C30ee) 45deg`; background cycling picks the
  theme's own `backgrounds/` and leaves the symlink pointing inside
  `~/.local/state/omarchy/current/theme/backgrounds/`.
