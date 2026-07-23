#!/usr/bin/env python3
"""Portable Open Image Prompts CLI and local gallery-session bridge.

The script locates the repository from its own resolved path (or
``OIP_REPO_ROOT``), delegates archive reads to ``scripts/prompt_library.py``,
and owns a loopback-only gallery process. It never writes the prompt database.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import http.client
import http.server
import json
import os
import re
import signal
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from pathlib import Path
from typing import Any


TAXONOMY_VERSION = "oip-visual-v2"
SESSION_SCHEMA = "oip-gallery-session-v1"
SESSION_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
LOOPBACK = "127.0.0.1"
DEFAULT_PORT = 4173


def json_print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def find_repository() -> Path:
    configured = os.environ.get("OIP_REPO_ROOT", "").strip()
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.extend([Path.cwd().resolve(), *Path.cwd().resolve().parents])
    candidates.extend(Path(__file__).resolve().parents)
    for candidate in candidates:
        if (candidate / "scripts" / "prompt_library.py").is_file() and (candidate / "web" / "package.json").is_file():
            return candidate.resolve()
    raise SystemExit(
        "Open Image Prompts repository not found. Install this skill by symlink "
        "from the repository or set OIP_REPO_ROOT to the repository path."
    )


def runtime_paths(repository: Path) -> dict[str, Path]:
    root = repository / ".oip"
    return {
        "root": root,
        "sessions": root / "sessions",
        "pid": root / "gallery.pid.json",
        "log": root / "gallery.log",
    }


def atomic_json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_library(repository: Path, arguments: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(repository / "scripts" / "prompt_library.py"), *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        message = completed.stderr.strip() or completed.stdout.strip() or "prompt library command failed"
        raise SystemExit(message)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit(f"prompt library returned invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise SystemExit("prompt library returned a non-object response")
    return add_absolute_paths(repository, payload)


def absolute_local_path(repository: Path, value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (repository / path).resolve()
    try:
        resolved.relative_to(repository)
    except ValueError:
        return ""
    return str(resolved)


def add_record_paths(repository: Path, record: object) -> None:
    if not isinstance(record, dict):
        return
    paths = record.get("image_paths")
    if isinstance(paths, list):
        record["absolute_image_paths"] = [
            resolved for value in paths if (resolved := absolute_local_path(repository, value))
        ]
    images = record.get("images")
    if not isinstance(images, dict):
        return
    for image in [images.get("representative"), *(images.get("items") or [])]:
        if not isinstance(image, dict):
            continue
        resolved = absolute_local_path(repository, image.get("local_path"))
        if resolved:
            image["absolute_local_path"] = resolved


def add_absolute_paths(repository: Path, payload: dict[str, Any]) -> dict[str, Any]:
    payload["repository_root"] = str(repository)
    add_record_paths(repository, payload.get("result"))
    for collection in ("results", "related_results"):
        for record in payload.get(collection) or []:
            add_record_paths(repository, record)
    return payload


def require_v2(payload: dict[str, Any]) -> None:
    active = str(payload.get("active_taxonomy_version") or "")
    version = str(payload.get("taxonomy_version") or active)
    if active != TAXONOMY_VERSION or version != TAXONOMY_VERSION:
        raise SystemExit(
            f"This skill requires {TAXONOMY_VERSION}; archive reported active={active or 'unknown'} "
            f"and result={version or 'unknown'}. Legacy fallback is disabled."
        )


def process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def read_pid_record(repository: Path) -> dict[str, Any] | None:
    path = runtime_paths(repository)["pid"]
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return record if isinstance(record, dict) else None


def fetch_health(port: int, timeout: float = 0.6) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(f"http://{LOOPBACK}:{port}/_oip/health", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload if isinstance(payload, dict) else None
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None


def server_status(repository: Path) -> dict[str, Any]:
    record = read_pid_record(repository)
    if not record:
        return {"status": "stopped"}
    pid = int(record.get("pid") or 0)
    port = int(record.get("port") or 0)
    if not process_exists(pid):
        with contextlib.suppress(OSError):
            runtime_paths(repository)["pid"].unlink()
        return {"status": "stopped", "stale_pid_removed": pid}
    health = fetch_health(port) if port else None
    owned = bool(
        health
        and health.get("instance_id") == record.get("instance_id")
        and int(health.get("pid") or 0) == pid
    )
    return {
        "status": "running" if owned else "unverified",
        "pid": pid,
        "port": port,
        "url": f"http://{LOOPBACK}:{port}/" if port else None,
        "instance_id": record.get("instance_id"),
    }


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind((LOOPBACK, 0))
        return int(handle.getsockname()[1])


def wait_for_server(repository: Path, expected_instance: str, timeout: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        record = read_pid_record(repository)
        if record and record.get("instance_id") == expected_instance:
            status = server_status(repository)
            if status.get("status") == "running":
                return status
        time.sleep(0.15)
    log_path = runtime_paths(repository)["log"]
    tail = ""
    with contextlib.suppress(OSError):
        tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-12:])
    raise SystemExit(f"gallery server did not become ready within {timeout:.0f}s" + (f"\n{tail}" if tail else ""))


def start_server(repository: Path, port: int) -> dict[str, Any]:
    existing = server_status(repository)
    if existing.get("status") == "running":
        if int(existing.get("port") or 0) != port:
            raise SystemExit(
                f"gallery server already runs on {existing.get('port')}; stop it before choosing port {port}"
            )
        return {**existing, "already_running": True}
    if existing.get("status") == "unverified":
        raise SystemExit("gallery PID is live but ownership cannot be verified; refusing to replace or stop it")

    npm = os.environ.get("OIP_NPM", "npm")
    if not (repository / "web" / "package.json").is_file():
        raise SystemExit("gallery frontend is missing: expected web/package.json in the repository")
    if not shutil.which(npm):
        raise SystemExit(f"gallery requires the npm executable {npm!r}")
    if not (repository / "web" / "node_modules" / ".bin" / "vite").is_file():
        raise SystemExit(
            "gallery dependencies are missing; run `npm run setup` in the "
            "repository first to fetch the complete LFS corpus and install dependencies"
        )

    paths = runtime_paths(repository)
    paths["root"].mkdir(parents=True, exist_ok=True)
    instance_id = str(uuid.uuid4())
    vite_port = free_loopback_port()
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_serve",
        "--port",
        str(port),
        "--vite-port",
        str(vite_port),
        "--instance-id",
        instance_id,
    ]
    with paths["log"].open("a", encoding="utf-8") as log:
        subprocess.Popen(
            command,
            cwd=repository,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    return wait_for_server(repository, instance_id)


def stop_server(repository: Path) -> dict[str, Any]:
    status = server_status(repository)
    if status.get("status") == "stopped":
        return status
    if status.get("status") != "running":
        raise SystemExit("gallery process ownership could not be verified; refusing to send a signal")
    pid = int(status["pid"])
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and process_exists(pid):
        time.sleep(0.1)
    if process_exists(pid):
        # Ownership was verified through the instance-specific health endpoint.
        os.kill(pid, signal.SIGKILL)
    with contextlib.suppress(OSError):
        runtime_paths(repository)["pid"].unlink()
    return {"status": "stopped", "pid": pid}


def wait_for_vite(process: subprocess.Popen[bytes], port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Vite exited before startup with code {process.returncode}")
        try:
            connection = http.client.HTTPConnection(LOOPBACK, port, timeout=0.5)
            connection.request("HEAD", "/")
            response = connection.getresponse()
            response.read()
            connection.close()
            if response.status < 500:
                return
        except OSError:
            pass
        time.sleep(0.15)
    raise RuntimeError("Vite did not become ready")


def make_proxy_handler(repository: Path, vite_port: int, instance_id: str):
    sessions = runtime_paths(repository)["sessions"]

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            self._handle()

        def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            self._handle()

        def _handle(self) -> None:
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path == "/_oip/health":
                self._send_json({
                    "status": "running",
                    "pid": os.getpid(),
                    "port": self.server.server_port,
                    "instance_id": instance_id,
                })
                return
            prefix = "/_oip/sessions/"
            if parsed.path.startswith(prefix):
                session_name = parsed.path[len(prefix):]
                session_id = session_name.removesuffix(".json")
                if session_name != f"{session_id}.json" or not SESSION_ID_RE.fullmatch(session_id):
                    self.send_error(404)
                    return
                path = sessions / f"{session_id}.json"
                try:
                    body = path.read_bytes()
                except OSError:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
            self._proxy_to_vite()

        def _send_json(self, payload: object) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _proxy_to_vite(self) -> None:
            connection = http.client.HTTPConnection(LOOPBACK, vite_port, timeout=60)
            headers = {key: value for key, value in self.headers.items() if key.casefold() != "host"}
            headers["Host"] = f"{LOOPBACK}:{vite_port}"
            try:
                connection.request(self.command, self.path, headers=headers)
                response = connection.getresponse()
                self.send_response(response.status, response.reason)
                skipped = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"}
                for key, value in response.getheaders():
                    if key.casefold() not in skipped:
                        self.send_header(key, value)
                self.send_header("Connection", "close")
                self.end_headers()
                if self.command != "HEAD":
                    while chunk := response.read(64 * 1024):
                        self.wfile.write(chunk)
            except (OSError, http.client.HTTPException):
                if not self.wfile.closed:
                    with contextlib.suppress(OSError):
                        self.send_error(502, "Local gallery upstream unavailable")
            finally:
                connection.close()
                self.close_connection = True

        def log_message(self, format_string: str, *args: object) -> None:
            if self.path != "/_oip/health":
                super().log_message(format_string, *args)

    return Handler


def serve(repository: Path, port: int, vite_port: int, instance_id: str) -> int:
    paths = runtime_paths(repository)
    npm_name = os.environ.get("OIP_NPM", "npm")
    npm = shutil.which(npm_name) or npm_name
    api_port = free_loopback_port()
    environment = os.environ.copy()
    environment["OIP_GALLERY_HMR_PORT"] = str(vite_port)
    environment["OIP_API_PORT"] = str(api_port)
    api = subprocess.Popen(
        [sys.executable, str(repository / "server" / "oip_api.py")],
        cwd=repository,
        env=environment,
        stdin=subprocess.DEVNULL,
    )
    vite = subprocess.Popen(
        [npm, "--prefix", str(repository / "web"), "run", "dev:web", "--", "--host", LOOPBACK, "--port", str(vite_port), "--strictPort"],
        cwd=repository,
        env=environment,
        stdin=subprocess.DEVNULL,
    )
    server: http.server.ThreadingHTTPServer | None = None
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if api.poll() is not None:
                raise SystemExit(f"gallery API exited with code {api.returncode}")
            try:
                with urllib.request.urlopen(
                    f"http://{LOOPBACK}:{api_port}/health",
                    timeout=0.5,
                ) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(0.1)
        else:
            raise SystemExit("gallery API did not become ready within 30 seconds")
        wait_for_vite(vite, vite_port)
        server = http.server.ThreadingHTTPServer((LOOPBACK, port), make_proxy_handler(repository, vite_port, instance_id))
        atomic_json_write(paths["pid"], {
            "pid": os.getpid(),
            "port": port,
            "vite_port": vite_port,
            "instance_id": instance_id,
            "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        })

        def stop_signal(_signum: int, _frame: object) -> None:
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, stop_signal)
        signal.signal(signal.SIGINT, stop_signal)
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        if server:
            server.server_close()
        if vite.poll() is None:
            vite.terminate()
            try:
                vite.wait(timeout=5)
            except subprocess.TimeoutExpired:
                vite.kill()
        if api.poll() is None:
            api.terminate()
            try:
                api.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api.kill()
        record = read_pid_record(repository)
        if record and record.get("instance_id") == instance_id:
            with contextlib.suppress(OSError):
                paths["pid"].unlink()
    return 0


def normalize_lang(value: str) -> tuple[str, str]:
    if value in {"zh", "zh-Hans"}:
        return "zh-Hans", "zh"
    return "en", "en"


def search_arguments(args: argparse.Namespace) -> list[str]:
    values = ["search", args.intent, "--limit", str(args.limit), "--max-prompt-chars", str(args.max_prompt_chars), "--max-tags", str(args.max_tags)]
    for name in ("tag", "author", "tool"):
        value = getattr(args, name, None)
        if value:
            values.extend([f"--{name}", value])
    return values


def parse_json_object(value: str | None, label: str) -> dict[str, Any]:
    if not value:
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as error:
        raise SystemExit(f"{label} must be valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return payload


def bounded_int(minimum: int, maximum: int):
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as error:
            raise argparse.ArgumentTypeError(
                f"must be an integer from {minimum} to {maximum}"
            ) from error
        if not minimum <= parsed <= maximum:
            raise argparse.ArgumentTypeError(f"must be from {minimum} to {maximum}")
        return parsed

    return parse


def create_gallery_session(repository: Path, args: argparse.Namespace) -> dict[str, Any]:
    search = run_library(repository, search_arguments(args))
    require_v2(search)
    results = [
        *(search.get("results") or []),
        *(search.get("related_results") or []),
    ][:args.limit]
    if not results:
        raise SystemExit("No references matched the requested intent; gallery session was not created.")
    requested_lang = args.lang
    if requested_lang == "auto":
        detected = str((search.get("parsed_intent") or {}).get("language") or "")
        requested_lang = "zh" if detected.startswith("zh") else "en"
    locale, url_lang = normalize_lang(requested_lang)
    references = []
    for rank, result in enumerate(results, start=1):
        tweet_id = str(result.get("tweet_id") or "").strip()
        if not tweet_id:
            continue
        references.append({
            "tweet_id": tweet_id,
            "rank": rank,
            "score": result.get("score"),
            "match_kind": result.get("match_kind") or "exact",
            "missing_constraints": result.get("missing_constraints") or [],
            "match_reasons": result.get("match_reasons") or [],
        })
    if not references:
        raise SystemExit("Search returned no stable tweet IDs; gallery session was not created.")
    focus = str(args.focus or references[0]["tweet_id"])
    if focus not in {reference["tweet_id"] for reference in references}:
        raise SystemExit("--focus must be one of the retrieved reference tweet IDs")

    derived = {
        "en": args.derived_en or "",
        "zh-Hans": args.derived_zh or "",
    }
    if args.derived_prompt:
        derived[locale] = args.derived_prompt
    session_id = str(uuid.uuid4())
    payload = {
        "schema_version": SESSION_SCHEMA,
        "taxonomy_version": TAXONOMY_VERSION,
        "session_id": session_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "intent": args.intent,
        "locale": locale,
        "creative_spec": parse_json_object(args.creative_spec, "--creative-spec"),
        "derived_prompt": derived,
        "references": references,
    }
    session_path = runtime_paths(repository)["sessions"] / f"{session_id}.json"
    atomic_json_write(session_path, payload)
    if not args.no_start:
        start_server(repository, args.port)
    query = urllib.parse.urlencode({"session": session_id, "focus": focus, "lang": url_lang})
    url = f"http://{LOOPBACK}:{args.port}/?{query}"
    status = server_status(repository)
    url_usable = status.get("status") == "running" and int(status.get("port") or 0) == args.port
    if args.open and url_usable:
        webbrowser.open(url)
    response = {
        "schema_version": SESSION_SCHEMA,
        "session_id": session_id,
        "session_path": str(session_path),
        "reference_count": len(references),
        "focus": focus,
        "url": url,
        "url_usable": url_usable,
        "server": status,
    }
    if not url_usable:
        response["start_command"] = (
            f"{sys.executable} {Path(__file__).resolve()} start --port {args.port}"
        )
    return response


def add_search_options(parser: argparse.ArgumentParser, *, include_lang: bool = False) -> None:
    parser.add_argument("--intent", required=True)
    if include_lang:
        parser.add_argument("--lang", choices=("auto", "en", "zh", "zh-Hans"), default="auto")
    parser.add_argument("--limit", type=bounded_int(1, 50), default=8, metavar="1..50")
    parser.add_argument("--tag")
    parser.add_argument("--author")
    parser.add_argument("--tool")
    parser.add_argument("--max-prompt-chars", type=bounded_int(200, 20000), default=1600)
    parser.add_argument("--max-tags", type=bounded_int(1, 50), default=12)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open Image Prompts v2 retrieval and local gallery sessions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="delegate a read-only v2 archive search")
    add_search_options(search)

    get = subparsers.add_parser("get", help="delegate a read-only lookup by tweet ID")
    get.add_argument("--id", required=True, dest="tweet_id")
    get.add_argument("--max-prompt-chars", type=bounded_int(200, 30000), default=20000)
    get.add_argument("--max-tags", type=bounded_int(1, 100), default=50)

    subparsers.add_parser("status", help="show v2 archive coverage and owned gallery state")

    start = subparsers.add_parser("start", help="start the owned loopback gallery server")
    start.add_argument("--port", type=int, default=DEFAULT_PORT)

    subparsers.add_parser("stop", help="stop only the instance verified by the owned PID and health token")

    gallery = subparsers.add_parser("gallery", help="create a ranked reference session and gallery URL")
    add_search_options(gallery, include_lang=True)
    gallery.add_argument("--focus")
    gallery.add_argument("--derived-prompt", help="derived prompt in --lang")
    gallery.add_argument("--derived-en")
    gallery.add_argument("--derived-zh")
    gallery.add_argument("--creative-spec", help="compact JSON object passed from the style skill")
    gallery.add_argument("--port", type=int, default=DEFAULT_PORT)
    gallery.add_argument("--no-start", action="store_true", help="write the session and print its URL without starting a server")
    gallery.add_argument("--open", action="store_true", help="open the URL after the owned server is ready")

    return parser


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "_serve":
        internal = argparse.ArgumentParser(add_help=False)
        internal.add_argument("--port", type=int, required=True)
        internal.add_argument("--vite-port", type=int, required=True)
        internal.add_argument("--instance-id", required=True)
        args = internal.parse_args(sys.argv[2:])
        return serve(find_repository(), args.port, args.vite_port, args.instance_id)
    args = build_parser().parse_args()
    repository = find_repository()
    if args.command == "search":
        payload = run_library(repository, search_arguments(args))
        require_v2(payload)
        json_print(payload)
        return 0
    if args.command == "get":
        payload = run_library(repository, ["get", args.tweet_id, "--max-prompt-chars", str(args.max_prompt_chars), "--max-tags", str(args.max_tags)])
        require_v2(payload)
        json_print(payload)
        return 0
    if args.command == "status":
        payload = run_library(repository, ["status"])
        require_v2(payload)
        payload["gallery_server"] = server_status(repository)
        json_print(payload)
        return 0
    if args.command == "start":
        json_print(start_server(repository, args.port))
        return 0
    if args.command == "stop":
        json_print(stop_server(repository))
        return 0
    if args.command == "gallery":
        json_print(create_gallery_session(repository, args))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
