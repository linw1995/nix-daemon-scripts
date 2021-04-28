import os
import platform
import plistlib
import subprocess
import tempfile
from pathlib import Path

import click


@click.command()
@click.option("--http-proxy", default="http://localhost:1081")
def config_proxy(http_proxy: str):
    if (system := platform.system()) != "Darwin":
        raise click.UsageError(f"Does not support {system = !r}")

    if os.geteuid() != 0:
        raise click.UsageError("Please re-run script with root")

    NAME = "org.nixos.nix-daemon"
    output = subprocess.check_output(
        [
            "sudo",
            "launchctl",
            "print",
            f"system/{NAME}",
        ],
    )
    plist_path = next(
        path[7:]
        for line in output.splitlines()
        if (path := line.lstrip()).startswith(b"path = ")
    ).decode()
    with Path(plist_path).open(mode="rb") as f:
        data = plistlib.load(f)

    data["EnvironmentVariables"]["http_proxy"] = http_proxy
    data["EnvironmentVariables"]["https_proxy"] = http_proxy

    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "org.nixos.nix-daemon.plist"
        with p.open("wb") as f:
            plistlib.dump(data, f, fmt=plistlib.FMT_XML)

        os.chmod(str(p), 0o755)
        subprocess.check_call(["sudo", "launchctl", "unload", plist_path])
        subprocess.check_call(["sudo", "launchctl", "load", str(p)])


if __name__ == "__main__":
    config_proxy()
