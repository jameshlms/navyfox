from __future__ import annotations

import os
import platform
import urllib.request
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_PLATFORM_RID: dict[tuple[str, str], tuple[str, str]] = {
    ("Linux", "x86_64"): ("linux-x64", "NavyFox.Native.so"),
    ("Linux", "aarch64"): ("linux-arm64", "NavyFox.Native.so"),
    ("Windows", "AMD64"): ("win-x64", "NavyFox.Native.dll"),
    ("Windows", "ARM64"): ("win-arm64", "NavyFox.Native.dll"),
    ("Darwin", "arm64"): ("osx-arm64", "NavyFox.Native.dylib"),
    ("Darwin", "x86_64"): ("osx-x64", "NavyFox.Native.dylib"),
}

_GITHUB_REPO = "jameshlms/navyfox"


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if os.environ.get("GITHUB_ACTIONS"):
            return  # binary is pre-populated by the CI download-artifact step

        key = (platform.system(), platform.machine())
        if key not in _PLATFORM_RID:
            raise RuntimeError(
                f"navyfox: unsupported platform {key[0]!r}/{key[1]!r}. "
                f"Supported: {list(_PLATFORM_RID)}"
            )

        rid, lib_name = _PLATFORM_RID[key]
        dest = Path(self.root) / "src" / "navyfox" / "_libs" / rid / lib_name

        if dest.exists():
            return  # pre-populated by CI or local build

        pkg_version = self.metadata.version
        asset = f"{rid}-{lib_name}"
        url = f"https://github.com/{_GITHUB_REPO}/releases/download/v{pkg_version}/{asset}"

        print(f"navyfox: downloading {asset} from GitHub release v{pkg_version}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(url) as resp:
                dest.write_bytes(resp.read())
        except Exception as exc:
            dest.unlink(missing_ok=True)
            raise RuntimeError(
                f"navyfox: failed to download native binary for {rid}.\n"
                f"  URL: {url}\n"
                f"  Cause: {exc}\n"
                f"  If building from source, run: "
                f"dotnet publish native/NavyFox.Native -r {rid} -c Release"
            ) from exc
