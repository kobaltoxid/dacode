import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from install_d2 import D2_MEMBER, asset_name, expected_checksum, install_d2


class D2InstallerTests(unittest.TestCase):
    def test_selects_release_archive_for_supported_platforms(self) -> None:
        self.assertEqual(asset_name("Darwin", "arm64"), "d2-v0.9.0-macos-arm64.tar.gz")
        self.assertEqual(asset_name("Linux", "x86_64"), "d2-v0.9.0-linux-amd64.tar.gz")

    def test_rejects_unsupported_platforms(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "does not support operating system"):
            asset_name("Windows", "AMD64")
        with self.assertRaisesRegex(RuntimeError, "does not support architecture"):
            asset_name("Linux", "riscv64")

    def test_reads_expected_release_checksum(self) -> None:
        asset = "d2-v0.9.0-linux-amd64.tar.gz"
        checksum = "a" * 64
        self.assertEqual(expected_checksum(f"{checksum}  {asset}\n", asset), checksum)
        with self.assertRaisesRegex(ValueError, "checksum is missing"):
            expected_checksum("", asset)

    def test_installs_verified_archive_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = asset_name("Darwin", "arm64")
            binary = b"#!/bin/sh\nprintf 'v0.9.0\\n'\n"
            archive_path = root / asset
            with tarfile.open(archive_path, "w:gz") as archive:
                member = tarfile.TarInfo(D2_MEMBER)
                member.mode = 0o755
                member.size = len(binary)
                archive.addfile(member, io.BytesIO(binary))
            archive_bytes = archive_path.read_bytes()
            checksum = hashlib.sha256(archive_bytes).hexdigest()
            requested_urls: list[str] = []

            def fetch(url: str, destination: Path) -> None:
                requested_urls.append(url)
                if url.endswith("SHA256SUMS"):
                    destination.write_text(f"{checksum}  {asset}\n", encoding="utf-8")
                else:
                    destination.write_bytes(archive_bytes)

            with patch("install_d2.shutil.which", return_value=None):
                installed = install_d2(root / "bin", "Darwin", "arm64", fetch=fetch)

            self.assertEqual(installed, root / "bin/d2")
            self.assertTrue(installed.stat().st_mode & 0o111)
            self.assertEqual(installed.read_bytes(), binary)
            self.assertTrue(requested_urls[0].endswith(asset))
            self.assertTrue(requested_urls[1].endswith("SHA256SUMS"))

    def test_rejects_bad_checksum_and_preserves_existing_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = asset_name("Darwin", "arm64")
            archive_path = root / asset
            with tarfile.open(archive_path, "w:gz") as archive:
                member = tarfile.TarInfo(D2_MEMBER)
                member.mode = 0o755
                member.size = 1
                archive.addfile(member, io.BytesIO(b"x"))
            archive_bytes = archive_path.read_bytes()

            def fetch_bad_checksum(url: str, destination: Path) -> None:
                if url.endswith("SHA256SUMS"):
                    destination.write_text(f"{'0' * 64}  {asset}\n", encoding="utf-8")
                else:
                    destination.write_bytes(archive_bytes)

            with patch("install_d2.shutil.which", return_value=None):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    install_d2(root / "new-bin", "Darwin", "arm64", fetch=fetch_bad_checksum)

            target = root / "existing-bin/d2"
            target.parent.mkdir()
            target.write_text("keep this file", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "refusing to replace"):
                install_d2(target.parent, "Darwin", "arm64")
            self.assertEqual(target.read_text(encoding="utf-8"), "keep this file")


if __name__ == "__main__":
    unittest.main()
