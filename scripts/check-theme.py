#!/usr/bin/env python3
"""Check the published theme, using only Python 3.11+'s standard library."""
from __future__ import annotations
import argparse
import re
import struct
import tomllib
import zlib
from pathlib import Path

SURFACES = ('background', 'dark_background', 'darker_background', 'lighter_background')
TEXT = ('foreground', 'dark_foreground', 'light_foreground', 'bright_foreground', 'accent', 'muted')
ANSI = ('red', 'yellow', 'orange', 'green', 'cyan', 'blue', 'magenta', 'brown',
        'bright_red', 'bright_yellow', 'bright_green', 'bright_cyan', 'bright_blue', 'bright_magenta')
COLOR_KEYS = tuple(dict.fromkeys((*SURFACES, *TEXT, 'selection', *ANSI)))
DENIED = {'alacritty.toml', 'foot.ini', 'ghostty.conf', 'kitty.conf', 'vscode.json'}
ICONS = {'Yaru', 'Yaru-blue', 'Yaru-dark', 'Yaru-magenta', 'Yaru-olive',
         'Yaru-prussiangreen', 'Yaru-purple', 'Yaru-red', 'Yaru-sage', 'Yaru-wartybrown', 'Yaru-yellow'}


def luminance(color):
    channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
    return sum(x * w for x, w in zip(linear, (.2126, .7152, .0722)))


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)))
    return (y + .05) / (x + .05)


def png_size(path):
    """Check chunk integrity as well as dimensions; reject truncated PNGs."""
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('invalid PNG signature')
    offset, size, image_data = 8, None, False
    while offset + 12 <= len(data):
        length = struct.unpack('>I', data[offset:offset+4])[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('truncated PNG chunk')
        kind = data[offset+4:offset+8]
        payload = data[offset+8:end-4]
        if zlib.crc32(kind + payload) & 0xffffffff != struct.unpack('>I', data[end-4:end])[0]:
            raise ValueError('PNG checksum mismatch')
        if offset == 8 and (kind != b'IHDR' or length != 13):
            raise ValueError('missing PNG header')
        if kind == b'IHDR':
            size = struct.unpack('>II', payload[:8])
        if kind == b'IDAT':
            image_data = True
        if kind == b'IEND':
            if length or end != len(data) or not image_data or not size or min(size) <= 0:
                raise ValueError('invalid PNG structure')
            return size
        offset = end
    raise ValueError('missing PNG end marker')


def audit(root):
    errors, rows = [], []
    try:
        colors = tomllib.loads((root / 'colors.toml').read_text())
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f'colors.toml: {exc}'], []
    if colors.get('mode') not in ('light', 'dark'):
        errors.append('mode must be light or dark')
    for key in COLOR_KEYS:
        if not isinstance(colors.get(key), str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', colors[key]):
            errors.append(f'{key}: expected a six-digit hex color')
    # Fail clearly before any arithmetic on malformed values.
    if errors:
        return errors, rows
    for role in TEXT + ANSI:
        surfaces = SURFACES if role in TEXT else ('background',)
        ratio, surface = min((contrast(colors[role], colors[s]), s) for s in surfaces)
        rows.append((role, colors[role], ratio, surface))
        if ratio < 4.5:
            errors.append(f'{role}: {ratio:.2f}:1 on {surface}; minimum 4.5:1')
    # Omarchy derives selection_foreground from bright_foreground. Check both.
    for role in ('foreground', 'bright_foreground'):
        if contrast(colors[role], colors['selection']) < 4.5:
            errors.append(f'{role}: insufficient contrast on selection')
    ramp = [luminance(colors[k]) for k in ('darker_background', 'dark_background', 'background', 'lighter_background')]
    if ramp != sorted(ramp):
        errors.append('background surface ramp must increase in luminance')
    for name in ('README.md', 'LICENSE', 'icons.theme', 'keyboard.rgb'):
        if not (root / name).is_file():
            errors.append(f'missing {name}')
    if (root / 'icons.theme').exists() and (root / 'icons.theme').read_text().strip() not in ICONS:
        errors.append('unknown icons.theme')
    if (root / 'keyboard.rgb').exists() and (root / 'keyboard.rgb').read_text().strip().lower() != colors['accent'][1:].lower():
        errors.append('keyboard.rgb must match accent')
    images = [root / n for n in ('preview.png', 'preview-unlock.png', 'unlock.png')]
    backgrounds = sorted((root / 'backgrounds').glob('*.png'))
    if not backgrounds:
        errors.append('backgrounds/ must contain at least one PNG')
    for path in images + backgrounds:
        try:
            w, h = png_size(path)
            if path.stat().st_size > 50 * 1024**2 or w * h > 40_000_000:
                errors.append(f'{path.name}: image exceeds catalog limits')
            if path.name == 'preview.png' and (w < 1000 or abs(w / h - 16 / 9) > .004):
                errors.append('preview.png must be at least 1000px wide and approximately 16:9')
        except (OSError, ValueError, struct.error) as exc:
            errors.append(f'{path.relative_to(root)}: {exc}')
    for path in root.rglob('*'):
        if any(part in ('.git', '__pycache__') for part in path.relative_to(root).parts):
            continue
        if path.is_symlink() or path.name.endswith('.lua') or path.name in DENIED:
            errors.append(f'unsupported installed-theme file: {path.relative_to(root)}')
    return errors, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('theme', nargs='?', default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument('--write-report', action='store_true', help='write docs/PALETTE.md after passing')
    args = parser.parse_args()
    errors, rows = audit(args.theme.resolve())
    for role, color, ratio, surface in rows:
        print(f'{role:20} {color} {ratio:5.2f}:1 on {surface}')
    if errors:
        print('\n'.join('FAIL: ' + error for error in errors))
        return 1
    if args.write_report:
        report = ['# Palette audit', '', 'Generated by `python3 scripts/check-theme.py --write-report`.', '',
                  'Text roles, including `muted`, are measured against every opaque surface; ANSI hues against the terminal background. Both text foregrounds are checked on selection. The threshold is 4.5:1. This does not certify every application or translucent surface.', '',
                  '| Role | Color | Lowest contrast | Surface |', '| --- | --- | --- | --- |']
        report += [f'| `{k}` | `{c}` | {r:.2f}:1 | `{s}` |' for k,c,r,s in rows]
        (args.theme / 'docs').mkdir(exist_ok=True)
        (args.theme / 'docs/PALETTE.md').write_text('\n'.join(report) + '\n')
    print('Palette, assets and package checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
