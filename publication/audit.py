"""Record upstream audit results for review; never represent findings as a clean scan."""
import json
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
reports = {}
for name, extra in [("all", []), ("runtime", ["--omit=dev"])]:
    result = subprocess.run(["npm", "audit", "--json", *extra], cwd=source, capture_output=True, text=True)
    assert result.returncode in (0, 1), result.stderr
    report = json.loads(result.stdout)
    assert "error" not in report and "metadata" in report
    reports[name] = {"audit_exit_code": result.returncode, "report": report}
    Path("npm-audit-" + name + ".json").write_text(json.dumps(reports[name], indent=2) + "\n")
summary = {name: value["report"]["metadata"]["vulnerabilities"] for name, value in reports.items()}
Path("security-review.json").write_text(json.dumps({"status": "review_required" if any(r["audit_exit_code"] for r in reports.values()) else "no_npm_advisories_reported", "review_snapshot_only": True, "audits": summary}, indent=2) + "\n")
print(json.dumps(summary))
if any(r["audit_exit_code"] for r in reports.values()):
    print("::warning::Upstream dependency audit has findings. This image is a review snapshot, not security clearance or deployment approval. See the retained audit reports.")
