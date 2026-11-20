#!/usr/bin/env python3
"""Install the pinned D2 release into a user-local bin directory."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable


VERSION = "v0.9.0"
RELEASE_URL = f"https://github.com/d2lang/d2/releases/download/{VERSION}"
D2_MEMBER = f"d2-{VERSION}/bin/d2"
Downloader = Callable[[str, Path], None]


def asset_name(system: str | None = None, machine: str | None = None) -> str:
    operating_system = system or platform.system()
    architecture = (machine or platform.machine()).lower()
    architectures = {
        "amd64": "amd64",
        "x86_64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }
    if architecture not in architectures:
        raise RuntimeError(f"D2 auto-install does not support architecture {architecture!r}")
    platforms = {"Darwin": "macos", "Linux": "linux"}
    if operating_system not in platforms:
        raise RuntimeError(f"D2 auto-install does not support operating system {operating_system!r}")
    return f"d2-{VERSION}-{platforms[operating_system]}-{architectures[architecture]}.tar.gz"


def expected_checksum(checksums: str, asset: str) -> str:
    for line in checksums.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[-1].lstrip("*") == asset:
            checksum = fields[0].lower()
            if len(checksum) == 64 and all(character in "0123456789abcdef" for character in checksum):
                return checksum
    raise ValueError(f"release checksum is missing or invalid for {asset}")


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "dacode-installer"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _version(executable: Path) -> str | None:
    try:
        result = subprocess.run([str(executable), "--version"], check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _extract_binary(archive_path: Path, output_path: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        try:
            member = archive.getmember(D2_MEMBER)
        except KeyError as exc:
            raise ValueError(f"D2 archive is missing {D2_MEMBER}") from exc
        if not member.isfile():
            raise ValueError(f"D2 archive entry is not a regular file: {D2_MEMBER}")
        source = archive.extractfile(member)
        if source is None:
            raise ValueError(f"could not read D2 archive entry: {D2_MEMBER}")
        with source, output_path.open("wb") as output:
            shutil.copyfileobj(source, output)
    output_path.chmod(0o755)


def install_d2(bin_dir: Path, system: str | None = None, machine: str | None = None, fetch: Downloader = download) -> Path:
    target = bin_dir / "d2"
    if target.exists():
        if _version(target) == VERSION:
            return target
        raise FileExistsError(f"refusing to replace existing D2 command: {target}")

    existing = shutil.which("d2")
    if existing and _version(Path(existing)) == VERSION:
        return Path(existing)

    asset = asset_name(system, machine)
    bin_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dacode-d2-") as temp_name:
        temp_dir = Path(temp_name)
        archive_path = temp_dir / asset
        checksum_path = temp_dir / "SHA256SUMS"
        binary_path = temp_dir / "d2"
        fetch(f"{RELEASE_URL}/{asset}", archive_path)
        fetch(f"{RELEASE_URL}/SHA256SUMS", checksum_path)

        expected = expected_checksum(checksum_path.read_text(encoding="utf-8"), asset)
        digest = sha256_file(archive_path)
        if digest != expected:
            raise ValueError(f"SHA-256 mismatch for {asset}")

        _extract_binary(archive_path, binary_path)
        if _version(binary_path) != VERSION:
            raise RuntimeError(f"downloaded D2 did not report {VERSION}")

        try:
            with binary_path.open("rb") as source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination)
            target.chmod(0o755)
        except FileExistsError as exc:
            raise FileExistsError(f"refusing to replace existing D2 command: {target}") from exc
        except Exception:
            target.unlink(missing_ok=True)
            raise

    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Install D2 v0.9.0 for DaCode diagram rendering.")
    parser.add_argument("--bin-dir", type=Path, default=Path.home() / ".local" / "bin")
    args = parser.parse_args()
    try:
        path = install_d2(args.bin_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"D2 install failed: {exc}", file=sys.stderr)
        return 1
    print(f"D2 {VERSION} is available at {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
