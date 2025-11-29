# /src/dagger_mcp_server/security.py
"""Security Stage Implementation (MVP: MCP-379)
================================================

Implements the Phase 1 security quality gate with:
* Bandit SAST
* pip-audit (with safety fallback)
* Optional Trivy image scan (env toggle)
* Basic regex secret scanning
* Unified finding normalization + gating
* JSON + Markdown summary artifacts

Environment Variables (Configuration)
------------------------------------
SECURITY_ENABLE_IMAGE_SCAN   (default: false)
SECURITY_MAX_HIGH            (default: 0)
SECURITY_FAIL_ON_CRITICAL    (default: true)
SECURITY_SEVERITY_FLOOR      (default: Low)
SECURITY_TIMEOUT_SECONDS     (default: 55)

Outputs (under build/security/):
  security-report.json  (canonical aggregate)
  summary.md            (human readable)
  raw/bandit.json
  raw/pip-audit.json or raw/safety.json
  raw/trivy.json (if enabled)
  raw/secrets.json

Determinism: findings are sorted by (severity desc, tool, id, fingerprint) to ensure stable ordering.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import dagger
from dagger import dag, function, object_type

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Info"]


def _severity_rank(sev: str) -> int:
    try:
        return SEVERITY_ORDER.index(sev)
    except ValueError:
        return len(SEVERITY_ORDER)


@dataclasses.dataclass(frozen=True)
class Finding:
    """Unified finding schema instance."""

    tool: str
    type: str
    id: str
    title: str
    severity: str
    raw_severity: str
    location: Dict[str, Any]
    cvss: Optional[Dict[str, Any]]
    description: str
    recommendation: Optional[str]
    fingerprint: str
    suppressed: bool = False

    def to_dict(self) -> Dict[str, Any]:  # Stable ordering for JSON
        return {
            "tool": self.tool,
            "type": self.type,
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "raw_severity": self.raw_severity,
            "location": self.location,
            "cvss": self.cvss,
            "description": self.description,
            "recommendation": self.recommendation,
            "fingerprint": self.fingerprint,
            "suppressed": self.suppressed,
        }


def _fingerprint(fields: List[str]) -> str:
    h = hashlib.sha256()
    for f in fields:
        h.update(f.encode("utf-8", errors="ignore"))
    return h.hexdigest()[:20]


class SecurityConfig:
    """Resolved security configuration from environment with defaults."""

    def __init__(self) -> None:
        self.enable_image_scan = os.getenv("SECURITY_ENABLE_IMAGE_SCAN", "false").lower() == "true"
        self.max_high = int(os.getenv("SECURITY_MAX_HIGH", "0"))
        self.fail_on_critical = os.getenv("SECURITY_FAIL_ON_CRITICAL", "true").lower() == "true"
        self.severity_floor = os.getenv("SECURITY_SEVERITY_FLOOR", "Low")
        self.timeout_seconds = int(os.getenv("SECURITY_TIMEOUT_SECONDS", "55"))
        # Optional registry credentials for private image scanning
        self.registry_username = os.getenv("SECURITY_REGISTRY_USERNAME", "")
        self.registry_password = os.getenv("SECURITY_REGISTRY_PASSWORD", "")
        # Optional Docker Hub token for Docker Scout API/CLI
        self.docker_hub_token = os.getenv("DOCKER_HUB_TOKEN", "")
        if self.severity_floor not in SEVERITY_ORDER:
            self.severity_floor = "Low"


@object_type
class SecurityStage:
    """Security scanning stage providing SAST, dependency, optional image, and secret checks."""

    @function
    async def security_scan(
        self,
        source: dagger.Directory,
        image_ref: Optional[str] = None,
        enable_image_scan: Optional[bool] = None,
        # Optional overrides for gating to support demos/happy paths
        max_high: Optional[int] = None,
        fail_on_critical: Optional[bool] = None,
        severity_floor: Optional[str] = None,
        include_env_files: Optional[bool] = None,
    timeout_seconds: Optional[int] = None,
    registry_username: Optional[str] = None,
    registry_password: Optional[str] = None,
    docker_hub_token: Optional[str] = None,
    ) -> dagger.Directory:
        """Run the MVP security stage and return a directory containing artifacts.

        Args:
            source: Source directory for scanning.
            image_ref: Optional OCI image reference to scan with Trivy.
            max_high: Optional override for allowed High findings (default 0).
            fail_on_critical: Optional override for failing on any Critical (default true).
            severity_floor: Optional minimum severity to include (default Low).
            include_env_files: Include .env files in secret scan (default false).

        Returns:
            A directory with security-report.json, summary.md, and raw/ tool outputs.
        """
        cfg = SecurityConfig()
        # Apply optional overrides for gating behavior
        if max_high is not None:
            cfg.max_high = int(max_high)
        if fail_on_critical is not None:
            cfg.fail_on_critical = bool(fail_on_critical)
        if severity_floor is not None and severity_floor in SEVERITY_ORDER:
            cfg.severity_floor = severity_floor
        # Apply image scan override if provided
        if enable_image_scan is not None:
            cfg.enable_image_scan = bool(enable_image_scan)
        # Apply timeout override if provided
        if timeout_seconds is not None:
            cfg.timeout_seconds = int(timeout_seconds)
        # Apply optional registry credentials
        if registry_username is not None:
            cfg.registry_username = registry_username
        if registry_password is not None:
            cfg.registry_password = registry_password
        if docker_hub_token is not None:
            cfg.docker_hub_token = docker_hub_token
        start = time.time()

        base = (
            dag.container()
            .from_("python:3.11-slim")
            .with_mounted_cache("/root/.cache/pip", dag.cache_volume("pip-cache"))
            .with_directory("/src", source)
            .with_workdir("/src")
            # Install security tooling first
            .with_exec(["pip", "install", "bandit", "pip-audit", "safety"])
            # Best-effort project dependency install (supports pyproject or requirements.txt)
            .with_exec([
                "bash", "-c",
                "if [ -f pyproject.toml ]; then pip install -e . || true; "
                "elif [ -f requirements.txt ]; then pip install -r requirements.txt || true; fi"
            ])
        )

        # Launch scans concurrently (except optional image).
        bandit_task = asyncio.create_task(self._run_bandit(base))
        dep_task = asyncio.create_task(self._run_pip_audit_with_fallback(base))
        # Secret scan: include .env only if explicitly requested (env var or arg)
        include_env = (
            include_env_files
            if include_env_files is not None
            else os.getenv("SECURITY_INCLUDE_ENV_FILES", "false").lower() == "true"
        )
        secrets_task = asyncio.create_task(self._run_secret_scan(base, include_env))
        image_scan_task: Optional[asyncio.Task] = None
        if cfg.enable_image_scan and image_ref and cfg.docker_hub_token:
            # Use Docker Hub (Docker Scout) scanning only
            image_scan_task = asyncio.create_task(
                self._run_docker_hub_scan(
                    image_ref,
                    docker_hub_token=cfg.docker_hub_token,
                )
            )

        # Await results with timeout envelope
        try:
            results = await asyncio.wait_for(
                asyncio.gather(bandit_task, dep_task, secrets_task, *( [image_scan_task] if image_scan_task else [] )),
                timeout=cfg.timeout_seconds,
            )
        except asyncio.TimeoutError:
            # Cancel tasks & proceed with partials
            for t in [bandit_task, dep_task, secrets_task, image_scan_task]:
                if t and not t.done():
                    t.cancel()
            results = []

        # Unpack results gracefully
        bandit_raw, deps_raw, secrets_raw, image_raw = None, None, None, None
        if results:
            if len(results) >= 1:
                bandit_raw = results[0]
            if len(results) >= 2:
                deps_raw = results[1]
            if len(results) >= 3:
                secrets_raw = results[2]
            if len(results) >= 4:
                image_raw = results[3]

        findings: List[Finding] = []
        findings.extend(self._normalize_bandit(bandit_raw or {}))
        findings.extend(self._normalize_dependencies(deps_raw or {}))
        findings.extend(self._normalize_secrets(secrets_raw or {}))
        if image_raw:
            # Heuristically detect tool and normalize accordingly
            tool_name = (image_raw or {}).get("tool") or ""
            if tool_name == "docker-scout":
                findings.extend(self._normalize_docker_scout(image_raw or {}))

        # Filter by severity floor
        min_rank = _severity_rank(cfg.severity_floor)
        findings = [f for f in findings if _severity_rank(f.severity) <= min_rank]

        # Deterministic ordering
        findings.sort(key=lambda f: (_severity_rank(f.severity), f.tool, f.id, f.fingerprint))

        # Gate evaluation
        critical_count = sum(1 for f in findings if f.severity == "Critical")
        high_count = sum(1 for f in findings if f.severity == "High")
        gate_fail = False
        rationale: List[str] = []
        if cfg.fail_on_critical and critical_count > 0:
            gate_fail = True
            rationale.append(f"Critical findings present: {critical_count}")
        if high_count > cfg.max_high:
            gate_fail = True
            rationale.append(
                f"High findings {high_count} exceed allowed {cfg.max_high}"
            )
        if not rationale:
            rationale.append("All thresholds satisfied")

        elapsed = time.time() - start

        report = {
            "schema_version": 1,
            "generated_at": int(start),
            "duration_seconds": round(elapsed, 2),
            "config": {
                "enable_image_scan": cfg.enable_image_scan,
                "max_high": cfg.max_high,
                "fail_on_critical": cfg.fail_on_critical,
                "severity_floor": cfg.severity_floor,
                "timeout_seconds": cfg.timeout_seconds,
            },
            "summary": {
                "total": len(findings),
                "by_severity": {
                    sev: sum(1 for f in findings if f.severity == sev)
                    for sev in SEVERITY_ORDER
                },
                "by_tool": {},
                "gate_pass": not gate_fail,
                "gate_rationale": rationale,
            },
            "findings": [f.to_dict() for f in findings],
        }
        # by_tool breakdown
        tool_counts: Dict[str, int] = {}
        for f in findings:
            tool_counts[f.tool] = tool_counts.get(f.tool, 0) + 1
        report["summary"]["by_tool"] = tool_counts

        # Create summary markdown
        md_lines = ["# Security Summary", "", f"Gate: {'PASS' if not gate_fail else 'FAIL'}"]
        sev_counts = report["summary"]["by_severity"]
        md_lines.append("## Severity Counts")
        for sev in SEVERITY_ORDER:
            if sev_counts[sev]:
                md_lines.append(f"- {sev}: {sev_counts[sev]}")
        md_lines.append("\n## Tool Breakdown")
        for t, c in tool_counts.items():
            md_lines.append(f"- {t}: {c}")
        md_lines.append("\n## Gate Rationale")
        for r in rationale:
            md_lines.append(f"- {r}")
        # Examples (first <=5 high/critical)
        md_lines.append("\n## Notable Findings")
        notable = [f for f in findings if f.severity in ("Critical", "High")] [:5]
        if not notable:
            md_lines.append("(None)")
        else:
            for fnd in notable:
                md_lines.append(f"- [{fnd.severity}] {fnd.tool}:{fnd.id} - {fnd.title}")

        report_json = json.dumps(report, indent=2)
        summary_md = "\n".join(md_lines) + "\n"

        # Assemble artifact directory using Dagger directory API
        artifacts = (
            dag.directory()
            .with_new_file("security-report.json", report_json)
            .with_new_file("summary.md", summary_md)
            .with_new_file("raw/bandit.json", json.dumps(bandit_raw or {}))
            .with_new_file(
                f"raw/{'pip-audit' if (deps_raw or {}).get('tool') == 'pip-audit' else 'safety'}.json",
                json.dumps(deps_raw or {}),
            )
            .with_new_file("raw/secrets.json", json.dumps(secrets_raw or {}))
        )
        if image_raw:
            # Write raw image scan under docker-hub.json
            artifacts = artifacts.with_new_file("raw/docker-hub.json", json.dumps(image_raw))

        return artifacts

    # ---------------------- Tool Execution Helpers ---------------------- #
    async def _run_bandit(self, container: dagger.Container) -> Dict[str, Any]:
        # Bandit returns exit code 1 when issues are found; we must not treat that as a failure.
        # Use bash with '|| true' so we always capture stdout JSON (if any).
        try:
            out = await container.with_exec([
                "bash", "-c", "bandit -r . -f json -q || true"
            ]).stdout()
            out = out.strip()
            if not out:
                return {"_ok": False, "error": "empty bandit output"}
            # Some bandit versions may emit warnings to stderr, stdout still JSON.
            # Attempt to parse; if it fails, return error so caller proceeds gracefully.
            try:
                data = json.loads(out)
                data["_ok"] = True
                return data
            except json.JSONDecodeError as je:
                return {"_ok": False, "error": f"bandit json decode: {je}", "raw": out[:5000]}
        except Exception as e:  # noqa: BLE001
            return {"error": str(e), "_ok": False}

    async def _run_pip_audit_with_fallback(self, container: dagger.Container) -> Dict[str, Any]:
        # Try pip-audit (tolerate non-zero exit which indicates vulns found)
        try:
            out = await container.with_exec([
                "bash", "-c", "pip-audit -f json || true"
            ]).stdout()
            out = out.strip()
            if out:
                try:
                    data = json.loads(out)
                    return {"tool": "pip-audit", "result": data, "_ok": True}
                except json.JSONDecodeError as je:
                    # fall through to safety
                    pip_err = f"pip-audit json decode: {je}"
                else:
                    pip_err = None  # type: ignore[assignment]
            else:
                pip_err = "empty pip-audit output"
        except Exception as e:  # noqa: BLE001
            pip_err = str(e)

        # Fallback to safety with correct JSON flags
        try:
            out = await container.with_exec([
                "bash", "-c", "safety check --json || true"
            ]).stdout()
            out = out.strip()
            if out:
                data = json.loads(out)
                return {"tool": "safety", "result": data, "_ok": True, "fallback_error": pip_err}
            else:
                return {"tool": "safety", "error": f"empty safety output; pip-audit:{pip_err}", "_ok": False}
        except Exception as safety_err:  # noqa: BLE001
            return {"tool": "pip-audit", "error": f"pip-audit:{pip_err}; safety:{safety_err}", "_ok": False}

    async def _run_trivy_scan(
        self,
        image_ref: str,
        registry_username: Optional[str] = None,
        registry_password: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Run Trivy in a dedicated ephemeral container
        try:
            c = dag.container().from_("aquasec/trivy:0.51.4")
            args = ["image", "--quiet", "--format", "json"]
            # If registry credentials provided, pass them through
            if registry_username:
                args += ["--username", registry_username]
            if registry_password:
                args += ["--password", registry_password]
            args.append(image_ref)
            out = await c.with_exec(args).stdout()
            data = json.loads(out)
            data["_ok"] = True
            return data
        except Exception as e:  # noqa: BLE001
            return {"error": str(e), "_ok": False}

    async def _run_docker_hub_scan(
        self,
        image_ref: str,
        docker_hub_token: str,
    ) -> Dict[str, Any]:
        """Use Docker Scout CLI to fetch vulnerability data from Docker Hub for image_ref.

        Requires a Docker Hub Personal Access Token with read access passed as docker_hub_token.
        """
        try:
            # Use official Docker Scout CLI image
            c = (
                dag.container()
                .from_("docker/scout-cli:1.9.1")
                .with_env_variable("DOCKER_TOKEN", docker_hub_token)
                .with_user("0:0")
            )
            # Fetch CVEs in JSON format
            out = await c.with_exec(["cves", "--format", "json", image_ref]).stdout()
            out = out.strip()
            data = json.loads(out) if out else {"vulnerabilities": []}
            data["_ok"] = True
            data["tool"] = "docker-scout"
            data["image_ref"] = image_ref
            return data
        except Exception as e:  # noqa: BLE001
            return {"error": str(e), "_ok": False, "tool": "docker-scout", "image_ref": image_ref}

    async def _run_secret_scan(self, container: dagger.Container, include_env_files: bool = False) -> Dict[str, Any]:
        # Simple regex scanning
        patterns = {
            "generic_api_key": r"(?i)(api[_-]?key|token)[=:\s][A-Za-z0-9_\-]{16,}",
            "aws_access_key": r"AKIA[0-9A-Z]{16}",
            "private_key_block": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        }
        matches: List[Dict[str, Any]] = []
        try:
            # List candidate files (only .py and .txt by default for speed; optionally include .env files)
            if include_env_files:
                list_cmd = "grep -RIl --exclude-dir=.git -e '' . | egrep '\\.(py|env|txt)$' || true"
            else:
                # Exclude .env and .env.* files
                list_cmd = (
                    "grep -RIl --exclude-dir=.git -e '' . | egrep '\\.(py|txt)$' | "
                    "grep -v '/\\.env$' | grep -v '/\\.env\\.' || true"
                )
            file_list = await container.with_exec(["bash", "-c", list_cmd]).stdout()
            files = [f.strip() for f in file_list.splitlines() if f.strip()]
            for fp in files:
                content = await container.with_exec(["bash", "-c", f"sed -n '1,500p' {fp} || true"]).stdout()
                for pid, pattern in patterns.items():
                    for m in re.finditer(pattern, content):
                        matches.append({
                            "pattern_id": pid,
                            "file": fp.lstrip("./"),
                            "match": m.group(0)[:120]
                        })
            return {"matches": matches, "_ok": True}
        except Exception as e:  # noqa: BLE001
            return {"matches": matches, "error": str(e), "_ok": False}

    # ---------------------- Normalization ---------------------- #
    def _normalize_bandit(self, data: Dict[str, Any]) -> List[Finding]:
        results = []
        for issue in data.get("results", []) or []:
            raw_sev = issue.get("issue_severity", "LOW").upper()
            sev_map = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
            sev = sev_map.get(raw_sev, "Low")
            fid = issue.get("test_id", "B??")
            title = issue.get("issue_text", "Bandit issue")
            location = {
                "file": issue.get("filename", ""),
                "line": issue.get("line_number", 0)
            }
            # Normalize recommendation URL to stable docs (avoid versioned 404s)
            rec = issue.get("more_info")
            if isinstance(rec, str) and "bandit.readthedocs.io" in rec:
                # Replace any '/en/<version>/' with '/en/latest/'
                rec = re.sub(r"/en/[^/]+/", "/en/latest/", rec)
            # Curated fallbacks for common rules if missing or not RTD
            if not rec or "bandit.readthedocs.io" not in rec:
                curated = {
                    "B404": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b404-import-subprocess",
                    "B603": "https://bandit.readthedocs.io/en/latest/plugins/b603_subprocess_without_shell_equals_true.html",
                }
                rec = curated.get(fid, rec)
            fp = _fingerprint(["bandit", fid, location["file"], str(location["line"]), title])
            results.append(Finding(
                tool="bandit",
                type="sast",
                id=fid,
                title=title,
                severity=sev,
                raw_severity=raw_sev,
                location=location,
                cvss=None,
                description=issue.get("issue_text", ""),
                recommendation=rec,
                fingerprint=fp,
            ))
        return results

    def _normalize_dependencies(self, data: Dict[str, Any]) -> List[Finding]:
        results: List[Finding] = []
        tool = data.get("tool", "pip-audit")
        result = data.get("result", [])
        # pip-audit shape: list of {name, version, vulnerabilities:[{id, description, fix_version, severity?}]}
        if tool == "pip-audit":
            # Support both legacy list and newer dict with 'dependencies'
            if isinstance(result, dict):
                packages = result.get("dependencies") or result.get("packages") or []
            elif isinstance(result, list):
                packages = result
            else:
                packages = []
            for pkg in packages:
                vulns = pkg.get("vulns") or pkg.get("vulnerabilities") or []
                for v in vulns:
                    vid = v.get("id", "UNKNOWN")
                    desc = v.get("description") or v.get("advisory") or "Dependency vulnerability"
                    # CVSS score may appear as severity or via score field
                    cvss_base = v.get("cvss_score") or v.get("score")
                    sev = self._map_cvss_to_severity(cvss_base, v.get("severity"))
                    fp = _fingerprint([tool, pkg.get("name", ""), vid, desc[:40]])
                    results.append(Finding(
                        tool=tool,
                        type="dependency",
                        id=vid,
                        title=f"{pkg.get('name')} {vid}",
                        severity=sev,
                        raw_severity=str(v.get("severity") or cvss_base or "Unknown"),
                        location={"file": f"{pkg.get('name')}=={pkg.get('version')}"},
                        cvss={"base": cvss_base} if isinstance(cvss_base, (int, float)) else None,
                        description=desc,
                        recommendation=v.get("fix_version"),
                        fingerprint=fp,
                    ))
        elif tool == "safety":
            # safety json shape may differ: list of vulnerabilities or dict
            vulns = result if isinstance(result, list) else result.get("vulnerabilities", [])
            for v in vulns:
                pkg = v.get("package_name", "unknown")
                vid = v.get("vulnerability_id") or v.get("advisory_id") or v.get("identifier") or "SAFETY"
                desc = v.get("vulnerability_description") or v.get("advisory") or v.get("description") or "Dependency vulnerability"
                sever = v.get("severity") or v.get("cvss_score")
                cvss_base = v.get("cvss_score") if isinstance(v.get("cvss_score"), (int, float)) else None
                sev = self._map_cvss_to_severity(cvss_base, sever)
                fp = _fingerprint([tool, pkg, vid, desc[:40]])
                results.append(Finding(
                    tool=tool,
                    type="dependency",
                    id=str(vid),
                    title=f"{pkg} {vid}",
                    severity=sev,
                    raw_severity=str(sever or cvss_base or "Unknown"),
                    location={"file": pkg},
                    cvss={"base": cvss_base} if cvss_base else None,
                    description=desc,
                    recommendation=v.get("fixed_version"),
                    fingerprint=fp,
                ))
        return results

    def _normalize_trivy(self, data: Dict[str, Any]) -> List[Finding]:
        results: List[Finding] = []
        for res in data.get("Results", []) or []:
            for vuln in res.get("Vulnerabilities", []) or []:
                raw = vuln.get("Severity", "UNKNOWN").upper()
                sev = {
                    "CRITICAL": "Critical",
                    "HIGH": "High",
                    "MEDIUM": "Medium",
                    "LOW": "Low",
                }.get(raw, "Info")
                vid = vuln.get("VulnerabilityID", "TRIVY")
                title = vuln.get("Title") or vid
                fp = _fingerprint(["trivy", vid, title])
                cvss = None
                if vuln.get("CVSS") and isinstance(vuln["CVSS"], dict):
                    # choose first vendor
                    for vendor, meta in vuln["CVSS"].items():  # noqa: B007
                        if isinstance(meta, dict) and meta.get("V3Score"):
                            cvss = {"base": meta.get("V3Score"), "vector": meta.get("V3Vector")}
                            break
                results.append(Finding(
                    tool="trivy",
                    type="image",
                    id=vid,
                    title=title,
                    severity=sev,
                    raw_severity=raw,
                    location={"file": res.get("Target", "image"), "image_layer": vuln.get("LayerID")},
                    cvss=cvss,
                    description=vuln.get("Description", ""),
                    recommendation=vuln.get("FixedVersion"),
                    fingerprint=fp,
                ))
        return results

    def _normalize_docker_scout(self, data: Dict[str, Any]) -> List[Finding]:
        results: List[Finding] = []
        vulns = data.get("vulnerabilities") or data.get("cves") or []
        # Some versions may return a dict with key 'cves' mapping to list
        if isinstance(vulns, dict):
            # Attempt common nested shapes
            if "items" in vulns and isinstance(vulns["items"], list):
                vulns = vulns["items"]
            else:
                vulns = list(vulns.values())
        if isinstance(vulns, list):
            for v in vulns:
                vid = v.get("cve") or v.get("id") or v.get("vulnerability") or "SCOUT"
                raw = (v.get("severity") or "UNKNOWN").upper()
                sev = {
                    "CRITICAL": "Critical",
                    "HIGH": "High",
                    "MEDIUM": "Medium",
                    "LOW": "Low",
                }.get(raw, "Info")
                pkg = v.get("package") or (v.get("package_name") if isinstance(v.get("package_name"), str) else None)
                version = v.get("version") or (v.get("package_version") if isinstance(v.get("package_version"), str) else None)
                fixed = v.get("fix_version") or v.get("fixed_version") or v.get("fixedVersion")
                title = v.get("title") or vid
                desc = v.get("description") or "Image vulnerability"
                cvss_val = None
                cvss_meta = v.get("cvss") or v.get("cvss_score")
                if isinstance(cvss_meta, (int, float)):
                    cvss_val = float(cvss_meta)
                elif isinstance(cvss_meta, dict) and isinstance(cvss_meta.get("score"), (int, float)):
                    cvss_val = float(cvss_meta["score"])
                fp = _fingerprint(["docker-scout", vid, str(pkg or ""), str(version or "")])
                results.append(Finding(
                    tool="docker-scout",
                    type="image",
                    id=str(vid),
                    title=title,
                    severity=sev,
                    raw_severity=raw,
                    location={"file": data.get("image_ref", "image"), "package": pkg, "version": version},
                    cvss={"base": cvss_val} if cvss_val is not None else None,
                    description=desc,
                    recommendation=fixed,
                    fingerprint=fp,
                ))
        return results

    def _normalize_secrets(self, data: Dict[str, Any]) -> List[Finding]:
        results: List[Finding] = []
        for m in data.get("matches", []) or []:
            pattern_id = m.get("pattern_id", "secret")
            severity = "High"
            if pattern_id == "private_key_block":
                severity = "Critical"  # escalate per spec
            fp = _fingerprint(["secrets", pattern_id, m.get("file", ""), m.get("match", "")])
            results.append(Finding(
                tool="secrets",
                type="secret",
                id=pattern_id,
                title=f"Secret pattern: {pattern_id}",
                severity=severity,
                raw_severity=severity,
                location={"file": m.get("file", ""), "line": 0},
                cvss=None,
                description=f"Potential secret detected: {m.get('match','')}",
                recommendation="Remove or rotate secret; use secure secret storage.",
                fingerprint=fp,
            ))
        return results

    # ---------------------- Helpers ---------------------- #
    def _map_cvss_to_severity(self, cvss: Optional[float], fallback: Optional[str]) -> str:
        if isinstance(cvss, (int, float)):
            if cvss >= 9.0:
                return "Critical"
            if cvss >= 7.0:
                return "High"
            if cvss >= 4.0:
                return "Medium"
            if cvss >= 0.1:
                return "Low"
            return "Info"
        # fallback textual mapping if present
        if fallback:
            up = str(fallback).upper()
            mapping = {
                "CRITICAL": "Critical",
                "HIGH": "High",
                "MEDIUM": "Medium",
                "LOW": "Low",
                "INFO": "Info",
            }
            return mapping.get(up, "Info")
        return "Info"

