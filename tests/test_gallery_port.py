"""Regression tests for gallery port selection.

A second checkout on the same machine used to be unusable: the gallery port was
fixed at 4173 with no fallback, the collision surfaced only as a raw traceback
after the full 30s startup timeout, and an explicit --port behaved the same way.
These tests pin the two behaviours that fix depends on.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import socket
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OIP_PATH = REPOSITORY_ROOT / "skills" / "img-gen-prompts" / "scripts" / "oip.py"


def load_oip(path: Path = OIP_PATH, name: str = "oip_cli"):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oip = load_oip()


@contextmanager
def clean_environment(**overrides: str | None):
    """Run with the given variables forced to a value, or removed when None."""
    previous = {key: os.environ.get(key) for key in overrides}
    for key, value in overrides.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class occupied_port:
    """Hold a real loopback listener so the probe sees a live collision."""

    def __enter__(self) -> int:
        self._handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._handle.bind((oip.LOOPBACK, 0))
        self._handle.listen(1)
        return int(self._handle.getsockname()[1])

    def __exit__(self, *_exception: object) -> None:
        self._handle.close()


class GalleryPortTests(unittest.TestCase):
    def test_port_available_reports_a_live_listener_as_taken(self):
        with occupied_port() as port:
            self.assertFalse(oip.port_available(port))
        # Released ports stay usable: the probe sets SO_REUSEADDR like the server.
        self.assertTrue(oip.port_available(port))

    def test_default_port_falls_back_instead_of_failing(self):
        with occupied_port() as port:
            original = oip.DEFAULT_PORT
            oip.DEFAULT_PORT = port
            try:
                resolved = oip.resolve_gallery_port(None)
            finally:
                oip.DEFAULT_PORT = original
        self.assertNotEqual(resolved, port)
        self.assertTrue(oip.port_available(resolved))

    def test_explicit_port_fails_fast_and_names_the_conflict(self):
        with occupied_port() as port:
            with self.assertRaises(SystemExit) as raised:
                oip.resolve_gallery_port(port)
        message = str(raised.exception)
        self.assertIn(str(port), message)
        self.assertIn("already in use", message)
        # The message has to be actionable for an agent, not just descriptive.
        self.assertIn("--port", message)

    def test_explicit_free_port_is_honoured_exactly(self):
        free = oip.free_loopback_port()
        self.assertEqual(oip.resolve_gallery_port(free), free)

    def test_idle_timeout_defaults_and_validates(self):
        with clean_environment(OIP_GALLERY_IDLE_TIMEOUT=None):
            self.assertEqual(oip.gallery_idle_timeout(), float(oip.DEFAULT_IDLE_TIMEOUT))
        for raw, expected in (("0", 0.0), ("90", 90.0)):
            with clean_environment(OIP_GALLERY_IDLE_TIMEOUT=raw):
                self.assertEqual(oip.gallery_idle_timeout(), expected)
        for invalid in ("soon", "-5"):
            with clean_environment(OIP_GALLERY_IDLE_TIMEOUT=invalid):
                with self.assertRaises(SystemExit):
                    oip.gallery_idle_timeout()


class RepositoryBootstrapTests(unittest.TestCase):
    def test_copied_skill_outside_a_checkout_says_where_to_get_the_repository(self):
        """`npx skills add -g` copies the script out of the checkout.

        find_repository() then has nothing to walk up to, and the old message
        named OIP_REPO_ROOT without ever saying where the repository comes from,
        which leaves an agent that only installed the Skill with no way forward.
        """
        with tempfile.TemporaryDirectory() as raw_temporary:
            temporary = Path(raw_temporary).resolve()
            copied = temporary / "oip.py"
            shutil.copyfile(OIP_PATH, copied)
            detached = load_oip(copied, name="oip_detached")
            previous_cwd = Path.cwd()
            os.chdir(temporary)
            try:
                with clean_environment(OIP_REPO_ROOT=None):
                    with self.assertRaises(SystemExit) as raised:
                        detached.find_repository()
            finally:
                os.chdir(previous_cwd)
        message = str(raised.exception)
        self.assertIn("OIP_REPO_ROOT", message)
        self.assertIn("git clone", message)
        self.assertIn("open-image-prompts", message)
        self.assertIn("data:pull", message)


if __name__ == "__main__":
    unittest.main()
