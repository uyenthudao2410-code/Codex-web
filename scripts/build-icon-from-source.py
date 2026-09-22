#!/usr/bin/env python3
"""Builds electron/app-icon.png and electron/app-icon.ico from docs/ICON.png."""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.stderr.write("Pillow (PIL) is not installed. Unable to build icon from source image.\n")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "docs" / "ICON.png"
PNG_PATH = ROOT / "electron" / "app-icon.png"
RENDERER_PNG = ROOT / "renderer" / "app-icon.png"
ICO_PATH = ROOT / "electron" / "app-icon.ico"

def build():
    if not SOURCE_PATH.is_file():
        sys.stderr.write(f"Source icon not found: {SOURCE_PATH}\n")
        sys.exit(2)

    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    RENDERER_PNG.parent.mkdir(parents=True, exist_ok=True)
    ICO_PATH.parent.mkdir(parents=True, exist_ok=True)

    resample_filter = getattr(Image, "Resampling", Image).LANCZOS
    img = Image.open(SOURCE_PATH).convert("RGBA")

    # Generate 512x512 PNG for Electron window, tray & renderer UI
    img_512 = img.resize((512, 512), resample_filter)
    img_512.save(PNG_PATH, format="PNG", optimize=True)
    img_512.save(RENDERER_PNG, format="PNG", optimize=True)

    # Generate multi-resolution ICO for Windows OS & installer
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ICO_PATH, format="ICO", sizes=sizes)

    print(f"Generated {PNG_PATH.relative_to(ROOT)}, {RENDERER_PNG.relative_to(ROOT)} and {ICO_PATH.relative_to(ROOT)} ({len(sizes)} sizes: 16-256) from {SOURCE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
