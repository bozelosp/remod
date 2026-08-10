#!/usr/bin/env python3
"""Local browser interface for REMOD analysis, comparison, and editing."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from math import isfinite
from pathlib import Path
from time import perf_counter
from urllib.parse import unquote, urlparse
import webbrowser

from json_stats import summarize_statistics
from remod_engine import (
    AnalysisCache,
    RemodelRequest,
    analyze_morphology,
    remodel_text,
)


REPOSITORY = Path(__file__).resolve().parent
UI_ROOT = REPOSITORY / "ui"
EXAMPLE_ROOT = REPOSITORY / "swc_files"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}
ANALYSIS_CACHE = AnalysisCache(max_entries=12)

PREVIEW_METRICS = {
    "all_arbor_total_length": ("Total arbor length", "units"),
    "all_arbor_total_area": ("Lateral arbor area", "units²"),
    "all_arbor_total_volume": ("Arbor volume", "units³"),
    "number_of_all_arbor_segments": ("Arbor segments", "count"),
    "number_of_all_terminal_arbor_segments": ("Terminal segments", "count"),
    "number_of_all_arbor_branchpoints": ("Branch points", "count"),
}


def _optional_number(value, *, integer: bool = False):
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValueError("numeric options cannot be true or false")
    number = float(value)
    if not isfinite(number):
        raise ValueError("numeric options must be finite")
    if integer:
        if not number.is_integer():
            raise ValueError("random seed must be a whole number")
        return int(number)
    return number


class RemodHandler(BaseHTTPRequestHandler):
    """Serve the dependency-free UI and its local JSON API."""

    server_version = "REMOD/2"

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data, allow_nan=False, separators=(",", ":")).encode()
        self._send(body, "application/json; charset=utf-8", status)

    def _request_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 100 * 1024 * 1024:
            raise ValueError("request body exceeds the 100 MB local limit")
        value = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in STATIC_FILES:
            file_name, content_type = STATIC_FILES[path]
            self._send((UI_ROOT / file_name).read_bytes(), content_type)
            return
        if path == "/api/health":
            self._json({"status": "ready", "analysis_cache": ANALYSIS_CACHE.info()})
            return
        if path == "/api/examples":
            self._json(
                {
                    "files": [
                        item.name for item in sorted(EXAMPLE_ROOT.glob("*.swc"))
                    ]
                }
            )
            return
        if path.startswith("/api/examples/"):
            name = unquote(path.removeprefix("/api/examples/"))
            candidate = EXAMPLE_ROOT / name
            if Path(name).name != name or candidate.suffix.lower() != ".swc":
                self._json({"error": "invalid example name"}, HTTPStatus.BAD_REQUEST)
                return
            if not candidate.is_file():
                self._json({"error": "example not found"}, HTTPStatus.NOT_FOUND)
                return
            self._send(candidate.read_bytes(), "text/plain; charset=utf-8")
            return
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            request = self._request_json()
            if path == "/api/workspace":
                self._workspace(request)
                return
            if path == "/api/remodel":
                self._remodel(request)
                return
            if path == "/api/groups":
                self._groups(request)
                return
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except OSError as exc:
            self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _workspace(self, request: dict) -> None:
        files = request.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("upload at least one SWC file")
        step = float(request.get("sholl_step", 20.0))
        started = perf_counter()
        analyses = []
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("each file must be an object")
            name = str(item["name"])
            content = str(item["content"])
            file_started = perf_counter()
            analysis, cached = ANALYSIS_CACHE.get_or_analyze(content, step)
            statistics = analysis.statistics
            analyses.append(
                {
                    "name": name,
                    "analysis_id": analysis.analysis_id,
                    "cached": cached,
                    "morphology": analysis.morphology,
                    "statistics": statistics,
                    "elapsed_ms": (perf_counter() - file_started) * 1000.0,
                }
            )
        self._json(
            {
                "files": analyses,
                "elapsed_ms": (perf_counter() - started) * 1000.0,
                "cache": ANALYSIS_CACHE.info(),
            }
        )

    def _groups(self, request: dict) -> None:
        files = request.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("group comparison requires analyzed morphologies")
        group_results: dict[str, dict[str, dict[str, object]]] = {"A": {}, "B": {}}
        seen_names: dict[str, set[str]] = {"A": set(), "B": set()}
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("each group member must be an object")
            name = str(item["name"])
            group = str(item.get("group", "A")).upper()
            if group not in group_results:
                raise ValueError(f"unknown comparison group: {group}")
            normalized_name = name.casefold()
            if normalized_name in seen_names[group]:
                raise ValueError(f"duplicate morphology name in cohort {group}: {name}")
            seen_names[group].add(normalized_name)
            statistics = ANALYSIS_CACHE.get_statistics(str(item["analysis_id"]))
            if statistics is None:
                raise ValueError(
                    f"analysis for {name} is no longer cached; analyze it again"
                )
            group_results[group][name] = statistics
        self._json(
            {
                "groups": {
                    group: summarize_statistics(results)
                    for group, results in group_results.items()
                    if results
                }
            }
        )

    def _remodel(self, request: dict) -> None:
        options = request.get("options", {})
        if not isinstance(options, dict):
            raise ValueError("options must be an object")
        step = float(request.get("sholl_step", 20.0))
        edit = RemodelRequest(
            file_name=str(request["name"]),
            who=str(options.get("who", "all_terminal")),
            action=str(options.get("action", "shrink")),
            random_ratio=float(options.get("random_ratio", 0.0)),
            manual_segments=str(options.get("manual_segments", "")),
            amount=_optional_number(options.get("amount")),
            extent_unit=str(options.get("extent_unit", "percent")),
            radius_change=_optional_number(options.get("radius_change")),
            radius_unit=str(options.get("radius_unit", "percent")),
            seed=_optional_number(options.get("seed"), integer=True),
        )
        started = perf_counter()
        source = str(request["content"])
        before, _cached = ANALYSIS_CACHE.get_or_analyze(source, step)
        result = remodel_text(source, edit, parsed=before.parsed)
        after = analyze_morphology(result.content, step, parsed=result.parsed)
        ANALYSIS_CACHE.store(after)
        statistics = after.statistics
        stem = Path(edit.file_name).stem
        output_stem = stem if stem.endswith("_remodeled") else f"{stem}_remodeled"
        output_name = f"{output_stem}.swc"
        changes = []
        for key, (label, unit) in PREVIEW_METRICS.items():
            previous = float(before.statistics[key])
            current = float(statistics[key])
            changes.append(
                {
                    "key": key,
                    "label": label,
                    "unit": unit,
                    "before": previous,
                    "after": current,
                    "delta": current - previous,
                    "percent": None
                    if previous == 0.0
                    else (current - previous) / abs(previous) * 100.0,
                }
            )
        warnings = []
        relevant_effects = {
            edit.action,
            "remodeling",
            "radius_edit" if edit.radius_change is not None else "",
        }
        for diagnostic in after.parsed.warnings:
            if relevant_effects.intersection(diagnostic.get("affects", [])):
                warnings.append(str(diagnostic["message"]))
        if edit.action == "remove":
            warnings.append("Removal includes every distal descendant of each target.")
        if edit.action in {"shrink", "extend", "scale"} and any(
            target not in before.parsed.all_terminal for target in result.targets
        ):
            warnings.append(
                "At least one target is nonterminal; its distal subtree is translated "
                "rigidly, which can change spatial and Sholl profiles."
            )
        if edit.seed is None and (
            edit.who.startswith("random_") or edit.action in {"extend", "branch"}
        ):
            warnings.append(
                "No random seed is set; another preview may select or generate different geometry."
            )
        if len(result.targets) > max(10, len(before.parsed.arbor_roots) // 2):
            warnings.append("This operation affects a broad portion of the arbor tree.")
        self._json(
            {
                "name": output_name,
                "content": result.content,
                "targets": result.targets,
                "selector": result.selector,
                "analysis_id": after.analysis_id,
                "morphology": after.morphology,
                "statistics": statistics,
                "changes": changes,
                "warnings": warnings,
                "impact": {
                    "samples_before": len(before.parsed.samples),
                    "samples_after": len(result.parsed.samples),
                    "segments_before": len(before.parsed.arbor_roots),
                    "segments_after": len(result.parsed.arbor_roots),
                },
                "elapsed_ms": (perf_counter() - started) * 1000.0,
            }
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run REMOD's local browser UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--no-open", action="store_true", help="Do not open the browser automatically"
    )
    return parser


def main(arguments: list[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    server = ThreadingHTTPServer((options.host, options.port), RemodHandler)
    url = f"http://{options.host}:{server.server_port}/"
    print(f"REMOD Studio is ready at {url}")
    if not options.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nREMOD Studio stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
