#!/usr/bin/env python3
"""Local browser interface for REMOD analysis, comparison, and editing."""

from __future__ import annotations

import argparse
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from math import isfinite
from pathlib import Path
from threading import BoundedSemaphore
from time import perf_counter
from urllib.parse import unquote, urlparse
import webbrowser

from json_stats import summarize_statistics
from remod.cli import _read_text
from remod.model import MAX_SWC_BYTES, _finite_token
from remod_engine import (
    AnalysisCache, RemodelRequest, analyze_morphology, remodel_text,
    validate_file_name,
)

REPOSITORY = Path(__file__).resolve().parent
UI_ROOT = REPOSITORY / "ui"
EXAMPLE_ROOT = REPOSITORY / "swc_files"
# Serve only the two intentional public examples, never arbitrary local SWCs.
EXAMPLES = ("0-2.CNG.swc", "0-2a.CNG.swc")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}
MAX_REQUEST_BYTES = 24 * 1024 * 1024
MAX_FILES = 128
REQUEST_TIMEOUT = 5
ANALYSIS_CACHE = AnalysisCache(max_entries=12)
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; "
       "img-src 'self' blob: data:; connect-src 'self'; font-src 'none'; "
       "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")

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
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("numeric options cannot be true or false, or containers")
    try:
        number = _finite_token(str(value))
    except ValueError as exc:
        raise ValueError(f"numeric options must be finite decimal numbers: {exc}") from exc
    if integer:
        exact = Decimal(str(value))
        if exact != exact.to_integral_value() or abs(exact) > 2**53 - 1:
            raise ValueError("random seed must be an exactly representable whole number")
        return int(exact)
    return number


def _decimal_token(token):
    # Keep the lexical value until integer options have been checked exactly.
    _finite_token(token)
    return Decimal(token)


def _remodeled_name(name):
    stem = Path(validate_file_name(name)).stem
    suffix = ".swc" if stem.endswith("_remodeled") else "_remodeled.swc"
    while len((stem + suffix).encode("utf-8")) > 240:
        stem = stem[:-1]
    return validate_file_name(stem + suffix)


def _text(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    return value


def _files(request):
    files = request.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise ValueError(f"request must contain 1–{MAX_FILES} files")
    if any(not isinstance(item, dict) for item in files):
        raise ValueError("each file must be an object")
    return files


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result or key in {"__proto__", "prototype", "constructor"}:
            raise ValueError("duplicate or reserved JSON property")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("JSON numbers must be finite")


class RemodServer(ThreadingHTTPServer):
    """Loopback-only server with bounded connections and computations."""

    daemon_threads = True
    request_queue_size = 8

    def __init__(self, port=8765):
        if type(port) is not int or not 0 <= port <= 65535:
            raise ValueError("port must be an integer between 0 and 65535")
        self.slots = BoundedSemaphore(8)
        self.computations = BoundedSemaphore(2)
        super().__init__(("127.0.0.1", port), RemodHandler)
        self.hosts = {f"127.0.0.1:{self.server_port}", f"localhost:{self.server_port}"}

    def verify_request(self, request, address):
        return address[0] == "127.0.0.1"

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()

    def handle_error(self, request, address):
        # Do not disclose request content, filenames, or tracebacks.
        print("REMOD request failed; connection closed.")


class RemodHandler(BaseHTTPRequestHandler):
    """Serve fixed local assets and strict same-origin JSON routes."""

    def setup(self):
        self.request.settimeout(REQUEST_TIMEOUT)
        super().setup()

    def log_message(self, format, *args):
        pass

    def _send(self, body, content_type, status=200):
        self.close_connection = True
        self.send_response_only(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data, status=200):
        body = json.dumps(data, allow_nan=False, separators=(",", ":")).encode("utf-8")
        self._send(body, "application/json; charset=utf-8", status)

    def send_error(self, code, message=None, explain=None):
        self._json({"error": HTTPStatus(code).phrase}, code)

    def parse_request(self):
        if not super().parse_request():
            return False
        for header in ("Host", "Origin", "Content-Length", "Content-Type",
                       "Content-Encoding", "Sec-Fetch-Site", "X-Remod-Request"):
            if len(self.headers.get_all(header, [])) > 1:
                self.send_error(400)
                return False
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if (host not in self.server.hosts
            or (origin is not None and origin != "http://" + host)
            or self.headers.get("Sec-Fetch-Site", "none") not in {"none", "same-origin"}):
            self.send_error(403)
            return False
        if (not self.path.startswith("/") or self.path.startswith("//")
            or self.headers.get("Transfer-Encoding") is not None
            or self.headers.get("Content-Encoding") is not None
            or self.headers.get("Expect") is not None):
            self.send_error(400)
            return False
        if self.command not in {"GET", "POST"}:
            self.send_error(405)
            return False
        if self.command == "GET" and self.headers.get("Content-Length", "0") != "0":
            self.send_error(400)
            return False
        return True

    def _request_json(self):
        length_text = self.headers.get("Content-Length")
        if length_text is None:
            raise ValueError("Content-Length is required")
        if not length_text.isascii() or not length_text.isdecimal() or len(length_text) > 9:
            raise ValueError("Content-Length must be a nonnegative decimal integer")
        length = int(length_text)
        if not 0 < length <= MAX_REQUEST_BYTES:
            raise ValueError(f"JSON body must contain 1–{MAX_REQUEST_BYTES} bytes")
        content_type = self.headers.get("Content-Type", "").lower().replace(" ", "")
        if content_type not in {"application/json", "application/json;charset=utf-8"}:
            raise ValueError("Content-Type must be application/json with UTF-8 encoding")
        if self.headers.get("X-Remod-Request") != "1":
            raise ValueError("X-Remod-Request: 1 is required")
        body = self.rfile.read(length)
        if len(body) != length:
            raise ValueError("incomplete request body")
        value = json.loads(body.decode("utf-8"), parse_float=_decimal_token,
                           parse_constant=_constant, object_pairs_hook=_object)
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        pending = [(value, 0)]
        while pending:
            item, depth = pending.pop()
            if depth > 8:
                raise ValueError("JSON nesting exceeds 8 levels")
            if isinstance(item, (dict, list)):
                children = item.values() if isinstance(item, dict) else item
                pending.extend((child, depth + 1) for child in children)
        return value

    def do_GET(self):
        try:
            path = self.path
            if path in STATIC_FILES:
                name, content_type = STATIC_FILES[path]
                self._send(_read_text(UI_ROOT / name).encode("utf-8"), content_type)
            elif path == "/api/health":
                self._json({"status": "ready", "analysis_cache": ANALYSIS_CACHE.info()})
            elif path == "/api/examples":
                self._json({"files": list(EXAMPLES)})
            elif path.startswith("/api/examples/"):
                name = unquote(path.removeprefix("/api/examples/"), errors="strict")
                if name not in EXAMPLES:
                    self.send_error(404)
                    return
                self._send(_read_text(EXAMPLE_ROOT / name).encode("utf-8"), "text/plain; charset=utf-8")
            else:
                self.send_error(404)
        except (OSError, ValueError):
            self.send_error(500)

    def do_POST(self):
        if self.path not in {"/api/workspace", "/api/remodel", "/api/groups"}:
            self.send_error(404)
            return
        acquired = False
        try:
            request = self._request_json()
            acquired = self.server.computations.acquire(blocking=False)
            if not acquired:
                self.send_error(503)
                return
            route = {"/api/workspace": self._workspace,
                     "/api/remodel": self._remodel, "/api/groups": self._groups}
            route[self.path](request)
        except TimeoutError:
            self.send_error(408)
        except (KeyError, TypeError, ValueError, RecursionError, OverflowError) as exc:
            message = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, UnicodeError) else "invalid request"
            self._json({"error": message}, 400)
        except Exception:
            self.send_error(500)
        finally:
            if acquired:
                self.server.computations.release()

    def _workspace(self, request: dict) -> None:
        files = _files(request)
        step = _optional_number(request.get("sholl_step", 20.0))
        started = perf_counter()
        analyses = []
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("each file must be an object")
            name = validate_file_name(item["name"])
            content = _text(item["content"], "SWC content")
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
        files = _files(request)
        group_results: dict[str, dict[str, dict[str, object]]] = {"A": {}, "B": {}}
        seen_names: dict[str, set[str]] = {"A": set(), "B": set()}
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("each group member must be an object")
            name = validate_file_name(item["name"])
            group = _text(item.get("group", "A"), "group").upper()
            if group not in group_results:
                raise ValueError(f"unknown comparison group: {group}")
            normalized_name = name.casefold()
            if normalized_name in seen_names[group]:
                raise ValueError(f"duplicate morphology name in cohort {group}: {name}")
            seen_names[group].add(normalized_name)
            statistics = ANALYSIS_CACHE.get_statistics(_text(item["analysis_id"], "analysis ID"))
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
        step = _optional_number(request.get("sholl_step", 20.0))
        edit = RemodelRequest(
            file_name=validate_file_name(request["name"]),
            who=str(options.get("who", "all_terminal")),
            action=str(options.get("action", "shrink")),
            random_ratio=_optional_number(options.get("random_ratio", 0.0)),
            manual_segments=str(options.get("manual_segments", "")),
            amount=_optional_number(options.get("amount")),
            extent_unit=str(options.get("extent_unit", "percent")),
            radius_change=_optional_number(options.get("radius_change")),
            radius_unit=str(options.get("radius_unit", "percent")),
            seed=_optional_number(options.get("seed"), integer=True),
        )
        started = perf_counter()
        source = _text(request["content"], "SWC content")
        before, _cached = ANALYSIS_CACHE.get_or_analyze(source, step)
        result = remodel_text(source, edit, parsed=before.parsed)
        after = analyze_morphology(result.content, step, parsed=result.parsed)
        ANALYSIS_CACHE.store(after)
        statistics = after.statistics
        output_name = _remodeled_name(edit.file_name)
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
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--no-open", action="store_true", help="Do not open the browser automatically"
    )
    return parser


def main(arguments: list[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    server = RemodServer(options.port)
    url = f"http://127.0.0.1:{server.server_port}/"
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
