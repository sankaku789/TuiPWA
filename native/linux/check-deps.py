#!/usr/bin/env python3
"""Report common missing build dependencies before downloading or compiling."""
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


TOOLS = {
    "rustc": "Rust (stable / edition 2024)",
    "cargo": "Cargo",
    "make": "Make",
    "pkg-config": "pkg-config",
    "curl": "curl",
    "patch": "patch",
    "tar": "tar",
    "xz": "xz",
    "sha256sum": "SHA-256 ツール",
    "readelf": "binutils",
}

# pkg-config identifiers, not distribution-specific package names.
LIBRARIES = {
    "gio-2.0": "GLib / GIO / GObject",
    "gtk4": "GTK 4",
    "libadwaita-1": "libadwaita",
    "gtk4-layer-shell-0": "gtk4-layer-shell",
    "wayland-client": "Wayland クライアント",
    "x11": "X11",
    "egl": "EGL",
    "fontconfig": "fontconfig",
    "freetype2": "FreeType",
}

DISTRO_FAMILIES = {
    "arch": frozenset({
        "arch", "artix", "cachyos", "endeavouros", "garuda", "manjaro", "steamos",
    }),
    "debian": frozenset({
        "debian", "elementary", "kali", "linuxmint", "mx", "pop", "raspbian",
        "ubuntu", "zorin",
    }),
    "redhat": frozenset({
        "almalinux", "bazzite", "centos", "fedora", "nobara", "ol", "rhel", "rocky",
    }),
}

DISTRO_PROFILES = {
    "arch": {
        "label": "Arch 系",
        "install_cmd": "sudo pacman -S --needed",
        "packages": {
            "cc": "gcc",
            "make": "make",
            "pkg-config": "pkgconf",
            "curl": "curl",
            "patch": "patch",
            "tar": "tar",
            "xz": "xz",
            "sha256sum": "coreutils",
            "readelf": "binutils",
            "gio-2.0": "glib2",
            "gtk4": "gtk4",
            "libadwaita-1": "libadwaita",
            "gtk4-layer-shell-0": "gtk4-layer-shell",
            "wayland-client": "wayland",
            "x11": "libx11",
            "egl": "libglvnd",
            "fontconfig": "fontconfig",
            "freetype2": "freetype2",
        },
    },
    "debian": {
        "label": "Debian / Ubuntu 系",
        "install_cmd": "sudo apt install",
        "packages": {
            "cc": "build-essential",
            "make": "build-essential",
            "pkg-config": "pkg-config",
            "curl": "curl",
            "patch": "patch",
            "tar": "tar",
            "xz": "xz-utils",
            "sha256sum": "coreutils",
            "readelf": "binutils",
            "gio-2.0": "libglib2.0-dev",
            "gtk4": "libgtk-4-dev",
            "libadwaita-1": "libadwaita-1-dev",
            "gtk4-layer-shell-0": "libgtk4-layer-shell-dev",
            "wayland-client": "libwayland-dev",
            "x11": "libx11-dev",
            "egl": "libegl-dev",
            "fontconfig": "libfontconfig-dev",
            "freetype2": "libfreetype-dev",
        },
    },
    "redhat": {
        "label": "Red Hat / Fedora 系",
        "install_cmd": "sudo dnf install",
        "packages": {
            "cc": "gcc",
            "make": "make",
            "pkg-config": "pkgconf-pkg-config",
            "curl": "curl",
            "patch": "patch",
            "tar": "tar",
            "xz": "xz",
            "sha256sum": "coreutils",
            "readelf": "binutils",
            "gio-2.0": "glib2-devel",
            "gtk4": "gtk4-devel",
            "libadwaita-1": "libadwaita-devel",
            "gtk4-layer-shell-0": "gtk4-layer-shell-devel",
            "wayland-client": "wayland-devel",
            "x11": "libX11-devel",
            "egl": "libglvnd-devel",
            "fontconfig": "fontconfig-devel",
            "freetype2": "freetype-devel",
        },
    },
}


@dataclass(frozen=True)
class MissingItem:
    key: str | None
    description: str


def detect_distro_family(os_release_text=None):
    """Identify the distro family from /etc/os-release content, or return None."""
    if os_release_text is None:
        try:
            os_release_text = Path("/etc/os-release").read_text(encoding="utf-8")
        except OSError:
            return None

    values = {}
    for line in os_release_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        if key not in ("ID", "ID_LIKE"):
            continue
        try:
            tokens = shlex.split(raw)
        except ValueError:
            tokens = [raw.strip().strip('"').strip("'")]
        values[key] = [token.lower() for part in tokens for token in part.split()]

    for field in ("ID", "ID_LIKE"):
        for token in values.get(field, ()):
            for family, names in DISTRO_FAMILIES.items():
                if token in names:
                    return family
    return None


def find_missing_items():
    missing = []
    raw_cc = os.environ.get("CC") or "cc"
    command = shlex.split(raw_cc)
    cc_bin = command[0] if command else "cc"
    if not shutil.which(cc_bin):
        key = "cc" if cc_bin in ("cc", "gcc") else None
        missing.append(MissingItem(key, f"コマンド: {cc_bin} — C コンパイラ (CC)"))

    for tool, label in TOOLS.items():
        if not shutil.which(tool):
            missing.append(MissingItem(tool, f"コマンド: {tool} — {label}"))

    if shutil.which("pkg-config"):
        for module, label in LIBRARIES.items():
            result = subprocess.run(
                ["pkg-config", "--exists", module], capture_output=True,
            )
            if result.returncode:
                missing.append(
                    MissingItem(module, f"開発ライブラリ: {label} (pkg-config: {module})")
                )
    return missing


def missing_dependencies():
    return [item.description for item in find_missing_items()]


def format_missing_report(items, family=None):
    profile = DISTRO_PROFILES.get(family) if family else None
    lines = ["ビルドに必要な依存が見つかりません:"]
    packages = []
    rust_missing = False
    pkg_config_missing = False

    for item in items:
        if item.key in ("rustc", "cargo"):
            rust_missing = True
        if item.key == "pkg-config":
            pkg_config_missing = True
        package = profile["packages"].get(item.key) if profile and item.key else None
        if package:
            packages.append(package)
            lines.append(f"  - {item.description} [パッケージ例: {package}]")
        else:
            lines.append(f"  - {item.description}")

    lines.append("")
    if profile and packages:
        unique_packages = list(dict.fromkeys(packages))
        lines.append(f"導入コマンド例（{profile['label']}）:")
        lines.append(f"  {profile['install_cmd']} {' '.join(unique_packages)}")
        lines.append("")
    elif not profile:
        lines.append("対応するツール・開発用パッケージ（-dev / -devel 等）を導入してください。")

    if rust_missing:
        lines.append(
            "Rust / Cargo は edition 2024 対応の stable ツールチェーンが必要です"
            "（https://www.rust-lang.org/tools/install）。"
        )
    if pkg_config_missing:
        lines.append(
            "pkg-config が未導入のため開発ライブラリの確認を省略しました。"
            "導入後に make check-deps を再実行してください。"
        )

    lines.extend([
        "導入済みの場合は PATH / PKG_CONFIG_PATH を確認してください。",
        "導入手順: README.md の「インストール」",
        "再確認: make check-deps（ダウンロード・ビルドは行いません）",
    ])
    return "\n".join(lines) + "\n"


def main():
    items = find_missing_items()
    if items:
        family = detect_distro_family()
        print(format_missing_report(items, family), file=sys.stderr, end="")
        return 1
    print("依存チェック OK（バージョン互換性・実行環境はビルド・起動時に確認します）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
