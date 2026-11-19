"""Build dependency diagnostics; no system packages are required by these tests."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "check_deps", Path(__file__).resolve().parents[2] / "native/linux/check-deps.py"
)
deps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deps)


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"CC": "cc"})
        self.env.start()
        self.addCleanup(self.env.stop)

    @patch.object(deps.shutil, "which", return_value="/usr/bin/tool")
    @patch.object(deps.subprocess, "run", return_value=subprocess.CompletedProcess([], 0))
    def test_all_present(self, run, which):
        self.assertEqual(deps.missing_dependencies(), [])
        self.assertEqual(run.call_count, len(deps.LIBRARIES))
        checked = {call.args[0][-1] for call in run.call_args_list}
        self.assertIn("gtk4-layer-shell-0", checked)
        self.assertIn("wayland-client", checked)
        self.assertIn("x11", checked)
        self.assertNotIn("spirv-cross-c-shared", checked)
        self.assertNotIn("oniguruma", checked)

    @patch.object(deps.shutil, "which", return_value=None)
    @patch.object(deps.subprocess, "run")
    def test_missing_pkg_config_skips_library_probes(self, run, which):
        missing = deps.missing_dependencies()
        self.assertIn("コマンド: pkg-config — pkg-config", missing)
        self.assertIn("コマンド: cargo — Cargo", missing)
        run.assert_not_called()

    @patch.object(deps, "detect_distro_family", return_value=None)
    @patch.object(deps.shutil, "which", side_effect=lambda name: None if name == "curl" else name)
    @patch.object(deps.subprocess, "run")
    def test_reports_commands_and_libraries_together_with_generic_fallback(
        self, run, which, detect
    ):
        run.side_effect = lambda args, **kwargs: subprocess.CompletedProcess(
            args, 1 if args[-1] in ("gtk4", "gtk4-layer-shell-0") else 0
        )
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(deps.main(), 1)
        text = output.getvalue()
        for expected in (
            "curl", "GTK 4", "gtk4-layer-shell-0", "-dev / -devel", "PKG_CONFIG_PATH"
        ):
            self.assertIn(expected, text)
        self.assertNotIn("導入コマンド例", text)

    @patch.object(deps.shutil, "which", return_value="/usr/bin/tool")
    @patch.object(deps.subprocess, "run", return_value=subprocess.CompletedProcess([], 0))
    def test_compiler_override(self, run, which):
        with patch.dict(os.environ, {"CC": "clang -O2"}):
            self.assertEqual(deps.missing_dependencies(), [])
        which.assert_any_call("clang")

    def test_detect_distro_family(self):
        self.assertEqual(deps.detect_distro_family('ID=arch\n'), "arch")
        self.assertEqual(
            deps.detect_distro_family('ID=endeavouros\nID_LIKE="arch"\n'), "arch"
        )
        self.assertEqual(
            deps.detect_distro_family('ID=ubuntu\nID_LIKE=debian\n'), "debian"
        )
        self.assertEqual(
            deps.detect_distro_family('ID=fedora\n'), "redhat"
        )
        self.assertEqual(
            deps.detect_distro_family('ID=rocky\nID_LIKE="rhel centos fedora"\n'),
            "redhat",
        )
        self.assertIsNone(deps.detect_distro_family('ID=alpine\n'))

    @patch.object(deps, "detect_distro_family", return_value="debian")
    @patch.object(
        deps.shutil,
        "which",
        side_effect=lambda name: None if name in ("cc", "make", "rustc") else name,
    )
    @patch.object(deps.subprocess, "run")
    def test_debian_package_hints_deduplicated_and_rust_separate(self, run, which, detect):
        run.side_effect = lambda args, **kwargs: subprocess.CompletedProcess(
            args, 1 if args[-1] == "gtk4-layer-shell-0" else 0
        )
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(deps.main(), 1)
        text = output.getvalue()
        self.assertIn("[パッケージ例: libgtk4-layer-shell-dev]", text)
        self.assertIn("sudo apt install build-essential libgtk4-layer-shell-dev", text)
        self.assertIn("edition 2024", text)

    @patch.object(deps, "detect_distro_family", return_value="arch")
    @patch.object(deps.shutil, "which", return_value="/usr/bin/tool")
    @patch.object(deps.subprocess, "run")
    def test_arch_package_hints(self, run, which, detect):
        run.side_effect = lambda args, **kwargs: subprocess.CompletedProcess(
            args, 1 if args[-1] in ("gtk4-layer-shell-0", "egl") else 0
        )
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(deps.main(), 1)
        text = output.getvalue()
        self.assertIn("sudo pacman -S --needed gtk4-layer-shell libglvnd", text)

    @patch.object(deps, "detect_distro_family", return_value="redhat")
    @patch.object(deps.shutil, "which", return_value="/usr/bin/tool")
    @patch.object(deps.subprocess, "run")
    def test_redhat_package_hints(self, run, which, detect):
        run.side_effect = lambda args, **kwargs: subprocess.CompletedProcess(
            args, 1 if args[-1] in ("gtk4-layer-shell-0", "x11", "egl") else 0
        )
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(deps.main(), 1)
        text = output.getvalue()
        self.assertIn(
            "sudo dnf install gtk4-layer-shell-devel libX11-devel libglvnd-devel", text
        )

    @patch.object(deps, "detect_distro_family", return_value="arch")
    @patch.object(
        deps.shutil, "which", side_effect=lambda name: None if name == "pkg-config" else name
    )
    @patch.object(deps.subprocess, "run")
    def test_pkg_config_missing_notes_recheck(self, run, which, detect):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(deps.main(), 1)
        text = output.getvalue()
        self.assertIn("sudo pacman -S --needed pkgconf", text)
        self.assertIn("開発ライブラリの確認を省略しました", text)
        run.assert_not_called()

    def test_every_profile_maps_all_non_rust_dependencies(self):
        expected_keys = (
            {"cc"}
            | (set(deps.TOOLS) - {"rustc", "cargo"})
            | set(deps.LIBRARIES)
        )
        for family, profile in deps.DISTRO_PROFILES.items():
            with self.subTest(family=family):
                self.assertEqual(set(profile["packages"]), expected_keys)


if __name__ == "__main__":
    unittest.main()
