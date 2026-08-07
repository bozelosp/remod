#!/usr/bin/env python3
"""Local browser interface for REMOD analysis, comparison, and editing."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from time import perf_counter
from urllib.parse import unquote, urlparse
import webbrowser

from json_stats import compute_statistics_for_morphology, summarize_statistics
from remod_engine import RemodelRequest, analyze_text, morphology_payload, remodel_text


REPOSITORY = Path(__file__).resolve().parent
UI_ROOT = REPOSITORY / "ui"
EXAMPLE_ROOT = REPOSITORY / "swc_files"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def _optional_number(value, *, integer: bool = False):
    if value in (None, ""):
        return None
    return int(value) if integer else float(value)


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
            self._json({"status": "ready"})
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
        group_results: dict[str, dict[str, dict[str, object]]] = {"A": {}, "B": {}}
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("each file must be an object")
            name = str(item["name"])
            content = str(item["content"])
            group = str(item.get("group", "A")).upper()
            if group not in group_results:
                raise ValueError(f"unknown comparison group: {group}")
            file_started = perf_counter()
            analysis = analyze_text(content, step)
            statistics = analysis["statistics"]
            group_results[group][name] = statistics  # type: ignore[assignment]
            analyses.append(
                {
                    "name": name,
                    "group": group,
                    "morphology": analysis["morphology"],
                    "statistics": statistics,
                    "elapsed_ms": (perf_counter() - file_started) * 1000.0,
                }
            )
        summaries = {
            group: summarize_statistics(results)
            for group, results in group_results.items()
            if results
        }
        self._json(
            {
                "files": analyses,
                "groups": summaries,
                "elapsed_ms": (perf_counter() - started) * 1000.0,
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
            manual_dendrites=str(options.get("manual_dendrites", "")),
            amount=_optional_number(options.get("amount")),
            extent_unit=str(options.get("extent_unit", "percent")),
            radius_change=_optional_number(options.get("radius_change")),
            radius_unit=str(options.get("radius_unit", "percent")),
            seed=_optional_number(options.get("seed"), integer=True),
        )
        started = perf_counter()
        result = remodel_text(str(request["content"]), edit)
        statistics = compute_statistics_for_morphology(result.parsed, step)
        stem = Path(edit.file_name).stem
        output_stem = stem if stem.endswith("_remodeled") else f"{stem}_remodeled"
        output_name = f"{output_stem}.swc"
        self._json(
            {
                "name": output_name,
                "content": result.content,
                "targets": result.targets,
                "selector": result.selector,
                "morphology": morphology_payload(result.parsed),
                "statistics": statistics,
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
