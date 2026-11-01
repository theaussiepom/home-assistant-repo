"""Build the selected upstream Dockerfile without modifying its build context."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
spec = json.loads((root / "publication/source.json").read_text())
source = Path(sys.argv[1]).resolve()
image = sys.argv[2]
assert spec["repository"] == "NickStallman/home-assistant-repo"
assert re.fullmatch(r"[0-9a-f]{40}", spec["revision"])
assert spec["platform"] == "linux/amd64" and spec["review_snapshot"] is True
assert re.fullmatch(r"ghcr.io/home-assistant/base:3\.22@sha256:[0-9a-f]{64}", spec["base_image"])
assert subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() == spec["revision"]
subprocess.run(["git", "-C", str(source), "diff", "--exit-code", "HEAD", "--"], check=True)
context = source / "winet-extractor"
assert not (context / ".env").exists() and not (context / "data").exists()
dockerfile = context / "Dockerfile"
assert "npm ci --ignore-scripts" in dockerfile.read_text()
publisher = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
args = ["docker", "build", "--platform", spec["platform"], "--build-arg", "BUILD_FROM=" + spec["base_image"],
        "--label", "org.opencontainers.image.source=https://github.com/theaussiepom/home-assistant-repo",
        "--label", "org.opencontainers.image.revision=" + spec["revision"],
        "--label", "org.opencontainers.image.version=" + spec["version"],
        "--label", "org.opencontainers.image.description=Unmodified upstream WiNet review snapshot; security review pending",
        "--label", "io.github.theaussiepom.upstream.repository=" + spec["repository"],
        "--label", "io.github.theaussiepom.publisher.revision=" + publisher,
        "--label", "org.opencontainers.image.base.name=" + spec["base_image"], "-t", image, str(context)]
subprocess.run(args, check=True)
config = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
assert config["Architecture"] == "amd64" and config["Os"] == "linux"
assert config["Config"]["Entrypoint"] == ["/init"]
assert config["Config"]["Cmd"] == ["/usr/src/app/run.sh"]
receipt = {**spec, "publisher_revision": publisher, "image_id": config["Id"],
           "upstream_dockerfile_sha256": hashlib.sha256(dockerfile.read_bytes()).hexdigest(),
           "upstream_lockfile_sha256": hashlib.sha256((context / "package-lock.json").read_bytes()).hexdigest(),
           "application_source_modified": False, "production_integration": False}
Path("image-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
