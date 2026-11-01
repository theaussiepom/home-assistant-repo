# WiNet image publication

This fork publishes an AMD64 image at `ghcr.io/theaussiepom/winet-extractor`.
The application and Dockerfile come unchanged from the exact upstream revision in
`source.json`. The initial revision is a **0.5.0 release-branch snapshot**, not a
released upstream main version. Local certificate patches are excluded.

Pull requests build and test without registry credentials. A reviewed change on
this fork's main branch publishes the exact tested image artifact. Only the
publishing job receives package-write permission. There is no scheduled upstream
tracking, floating `latest` tag or automatic HomeLab integration.

The workflow runs upstream's tests and lint, builds its original multi-stage
Dockerfile with a pinned Home Assistant base, checks the real s6 startup, and
tests discovery and fresh MQTT sensor values against synthetic services on an
internal Docker network. Only public upstream source enters the build context;
private configuration and credentials remain runtime inputs.

## Review status

These are **review snapshots**, not a claim of security clearance. npm audit exit
codes and full all-dependency/runtime reports are retained with each tested image.
Findings are visible as workflow warnings and in `security-review.json`; scanner
errors fail the job. This evidence collection deliberately does not certify an
upstream snapshot as clean or authorize its production use.

The initial upstream lockfile reports two high-severity runtime advisories:

- `follow-redirects`: GHSA-mrwp-f3q8-3g9p, possible credential forwarding across redirects.
- `zod`: GHSA-mrhx-c7xc-m3w5, possible memory exhaustion with oversized constrained collections.

Development dependency findings are recorded separately. No dependency or
application patch is applied to hide these results. Review and any dependency
remediation come before deciding to integrate an image into HomeLab.

## Publishing and consumption

Each main-branch run publishes a unique tag containing the upstream commit,
workflow run ID and attempt. Image labels record upstream and publisher revisions
and the pinned base. The package is associated with this WiNet fork. Make this
public-source-only package public so deployment can pull without a registry token.

Use the published **registry manifest digest**, not the local image content ID or
a floating branch/tag, when later selecting an image in another project. The
`homelab`, `homelab-stack` and `homelab-site` repositories are unchanged by this
workflow. No live inverter or production MQTT broker is contacted by its tests.
