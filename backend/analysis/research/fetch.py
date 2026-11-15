import http.client
import ipaddress
import socket
import ssl
import threading
import time
import posixpath
import zlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from urllib.parse import unquote, urljoin, urlsplit


ALLOWED_MIME_TYPES = {"text/html", "application/json", "application/ld+json", "text/plain"}
_domain_pacing_lock = threading.Lock()
_domain_last_request = {}
_outbound_capacity = threading.BoundedSemaphore(2)
_dns_capacity = threading.BoundedSemaphore(2)
_dns_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="research-dns")


class FetchError(Exception):
    def __init__(self, code, message=None):
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class FetchPolicy:
    hostname: str
    allowed_path_prefixes: tuple[str, ...]
    redirect_hostnames: tuple[str, ...]
    redirect_rules: dict = field(default_factory=dict)
    allowed_ports: tuple[int, ...] = (443,)
    enabled: bool = True
    max_redirects: int = 2
    max_decoded_bytes: int = 2 * 1024 * 1024
    max_wire_bytes: int = 2 * 1024 * 1024
    request_timeout_seconds: float = 20
    min_interval_seconds: float = 0


@dataclass
class FetchBudget:
    max_requests: int = 20
    max_pages_per_domain: int = 5
    deadline_monotonic: float = field(default_factory=lambda: time.monotonic() + 60)
    request_count: int = 0
    decoded_bytes: int = 0
    wire_bytes: int = 0
    redirect_count: int = 0
    domain_request_counts: dict = field(default_factory=dict)

    def consume_request(self, hostname):
        if self.request_count >= self.max_requests:
            raise FetchError("REQUEST_BUDGET_EXHAUSTED")
        if time.monotonic() >= self.deadline_monotonic:
            raise FetchError("JOB_DEADLINE_EXCEEDED")
        current = self.domain_request_counts.get(hostname, 0)
        if current >= self.max_pages_per_domain:
            raise FetchError("DOMAIN_PAGE_BUDGET_EXHAUSTED")
        self.domain_request_counts[hostname] = current + 1
        self.request_count += 1


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    content_type: str
    body: bytes
    wire_bytes: int
    redirect_count: int
    approved_ip: str


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, port, approved_ip, timeout):
        self.approved_ip = approved_ip
        super().__init__(host, port=port, timeout=timeout)

    def connect(self):
        self.sock = socket.create_connection((self.approved_ip, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, approved_ip, timeout):
        self.approved_ip = approved_ip
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context())

    def connect(self):
        raw = socket.create_connection((self.approved_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)


def default_resolver(hostname, port):
    addresses = []
    for item in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM):
        value = item[4][0]
        if value not in addresses:
            addresses.append(value)
    if not addresses:
        raise FetchError("DNS_EMPTY")
    return addresses


def default_connector(scheme, hostname, port, approved_ip, timeout):
    if scheme == "https":
        return _PinnedHTTPSConnection(hostname, port, approved_ip, timeout)
    return _PinnedHTTPConnection(hostname, port, approved_ip, timeout)


def validate_public_address(address):
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as exc:
        raise FetchError("INVALID_RESOLVED_ADDRESS") from exc
    if not parsed.is_global:
        raise FetchError("NON_PUBLIC_ADDRESS")
    return str(parsed)


def _canonical_hostname(value):
    try:
        return value.rstrip(".").encode("idna").decode("ascii").lower()
    except (UnicodeError, AttributeError) as exc:
        raise FetchError("INVALID_HOSTNAME") from exc


class SafeFetcher:
    def __init__(self, *, resolver=default_resolver, connector=default_connector, sleeper=time.sleep):
        self.resolver = resolver
        self.connector = connector
        self.sleeper = sleeper

    def _validated_destination(self, url, policy, *, redirect=False):
        try:
            parts = urlsplit(url)
            hostname = _canonical_hostname(parts.hostname)
            port = parts.port or (443 if parts.scheme == "https" else 80)
        except (ValueError, TypeError) as exc:
            raise FetchError("INVALID_URL") from exc
        if parts.scheme not in {"http", "https"}:
            raise FetchError("UNSUPPORTED_SCHEME")
        if parts.username is not None or parts.password is not None:
            raise FetchError("EMBEDDED_CREDENTIALS")
        primary = _canonical_hostname(policy.hostname)
        if not redirect and hostname != primary:
            raise FetchError("SOURCE_NOT_ALLOWED")
        rules = None
        if redirect and hostname != primary:
            rules = policy.redirect_rules.get(hostname)
            if rules is None and hostname in {_canonical_hostname(item) for item in policy.redirect_hostnames}:
                rules = {
                    "allowed_ports": list(policy.allowed_ports),
                    "allowed_path_prefixes": list(policy.allowed_path_prefixes),
                }
            if rules is None:
                raise FetchError("REDIRECT_NOT_ALLOWED")
        allowed_ports = tuple((rules or {}).get("allowed_ports", policy.allowed_ports))
        prefixes = tuple((rules or {}).get("allowed_path_prefixes", policy.allowed_path_prefixes))
        if port not in allowed_ports:
            raise FetchError("UNSUPPORTED_PORT")
        raw_path = parts.path or "/"
        lowered = raw_path.lower()
        if "\\" in raw_path or "\x00" in raw_path or any(code in lowered for code in ("%2e", "%2f", "%5c", "%25")):
            raise FetchError("AMBIGUOUS_PATH")
        path = unquote(raw_path)
        normalized = posixpath.normpath(path)
        if path.endswith("/") and not normalized.endswith("/"):
            normalized += "/"
        if not normalized.startswith("/") or normalized != path:
            raise FetchError("AMBIGUOUS_PATH")
        if not any(path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes):
            raise FetchError("PATH_NOT_ALLOWED")
        return parts, hostname, port

    @staticmethod
    def _remaining(deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FetchError("JOB_DEADLINE_EXCEEDED")
        return remaining

    def _pace(self, hostname, interval, deadline):
        if interval <= 0:
            return
        with _domain_pacing_lock:
            now = time.monotonic()
            remaining = interval - (now - _domain_last_request.get(hostname, 0))
            if remaining > 0:
                if remaining >= self._remaining(deadline):
                    raise FetchError("JOB_DEADLINE_EXCEEDED")
                self.sleeper(remaining)
            _domain_last_request[hostname] = time.monotonic()

    def _resolve(self, hostname, port, deadline):
        if not _dns_capacity.acquire(timeout=self._remaining(deadline)):
            raise FetchError("DNS_CAPACITY")
        future = _dns_executor.submit(self.resolver, hostname, port)
        future.add_done_callback(lambda _future: _dns_capacity.release())
        try:
            return future.result(timeout=self._remaining(deadline))
        except FutureTimeout as exc:
            raise FetchError("DNS_TIMEOUT") from exc
        except OSError as exc:
            raise FetchError("DNS_ERROR") from exc

    def fetch(self, url, policy, budget):
        if not policy.enabled:
            raise FetchError("SOURCE_DISABLED")
        current = url
        redirects = 0
        while True:
            parts, hostname, port = self._validated_destination(current, policy, redirect=redirects > 0)
            budget.consume_request(hostname)
            request_deadline = min(budget.deadline_monotonic, time.monotonic() + policy.request_timeout_seconds)
            addresses = [validate_public_address(item) for item in self._resolve(hostname, port, request_deadline)]
            if not addresses:
                raise FetchError("DNS_EMPTY")
            self._pace(hostname, policy.min_interval_seconds, request_deadline)
            if not _outbound_capacity.acquire(timeout=self._remaining(request_deadline)):
                raise FetchError("OUTBOUND_CAPACITY")
            connection = None
            try:
                approved_ip = addresses[0]
                connection = self.connector(parts.scheme, hostname, port, approved_ip, self._remaining(request_deadline))
                path = parts.path or "/"
                if parts.query:
                    path += "?" + parts.query
                connection.request(
                    "GET",
                    path,
                    headers={
                        "Host": hostname if port in {80, 443} else f"{hostname}:{port}",
                        "User-Agent": "BeforebuyResearch/0.1 (+https://github.com/medyrad/beforebuy)",
                        "Accept": "text/html,application/json,application/ld+json,text/plain",
                        "Accept-Encoding": "gzip",
                        "Cookie": "",
                    },
                )
                if getattr(connection, "sock", None) is not None:
                    connection.sock.settimeout(self._remaining(request_deadline))
                response = connection.getresponse()
                location = response.getheader("Location")
                if response.status in {301, 302, 303, 307, 308}:
                    if not location:
                        raise FetchError("REDIRECT_WITHOUT_LOCATION")
                    if redirects >= policy.max_redirects:
                        raise FetchError("TOO_MANY_REDIRECTS")
                    redirects += 1
                    budget.redirect_count += 1
                    current = urljoin(current, location)
                    self._validated_destination(current, policy, redirect=True)
                    continue
                raw_content_type = response.getheader("Content-Type", "")
                content_type = raw_content_type.split(";", 1)[0].strip().lower()
                if not 200 <= response.status < 300:
                    raise FetchError("HTTP_STATUS")
                if content_type not in ALLOWED_MIME_TYPES:
                    raise FetchError("UNSUPPORTED_MIME")
                body, wire_bytes = self._read_bounded(
                    response, policy.max_decoded_bytes, policy.max_wire_bytes, budget, request_deadline
                )
                return FetchResult(current, response.status, content_type, body, wire_bytes, redirects, approved_ip)
            except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
                raise FetchError("TRANSPORT_ERROR") from exc
            finally:
                if connection is not None:
                    connection.close()
                _outbound_capacity.release()

    @staticmethod
    def _read_bounded(response, limit, wire_limit, budget, deadline_monotonic):
        chunks = []
        wire_bytes = 0
        encoding = (response.getheader("Content-Encoding", "") or "").lower()
        decompressor = None
        if encoding == "gzip":
            decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        elif encoding not in {"", "identity"}:
            raise FetchError("UNSUPPORTED_ENCODING")
        decoded = 0
        while True:
            remaining = deadline_monotonic - time.monotonic()
            if remaining <= 0:
                raise FetchError("JOB_DEADLINE_EXCEEDED")
            if getattr(response, "fp", None) is not None and getattr(response.fp, "raw", None) is not None:
                raw_socket = getattr(response.fp.raw, "_sock", None)
                if raw_socket is not None:
                    raw_socket.settimeout(remaining)
            reader = getattr(response, "read1", response.read)
            chunk = reader(64 * 1024)
            if time.monotonic() >= deadline_monotonic:
                raise FetchError("JOB_DEADLINE_EXCEEDED")
            if not chunk:
                break
            wire_bytes += len(chunk)
            budget.wire_bytes += len(chunk)
            if wire_bytes > wire_limit:
                raise FetchError("WIRE_RESPONSE_TOO_LARGE")
            try:
                piece = decompressor.decompress(chunk, limit - decoded + 1) if decompressor else chunk
            except zlib.error as exc:
                raise FetchError("MALFORMED_GZIP") from exc
            decoded += len(piece)
            budget.decoded_bytes += len(piece)
            if decoded > limit:
                raise FetchError("RESPONSE_TOO_LARGE")
            chunks.append(piece)
        if decompressor:
            if not decompressor.eof or decompressor.unused_data or decompressor.unconsumed_tail:
                raise FetchError("MALFORMED_GZIP")
            try:
                piece = decompressor.flush(limit - decoded + 1)
            except zlib.error as exc:
                raise FetchError("MALFORMED_GZIP") from exc
            decoded += len(piece)
            budget.decoded_bytes += len(piece)
            if decoded > limit:
                raise FetchError("RESPONSE_TOO_LARGE")
            chunks.append(piece)
        return b"".join(chunks), wire_bytes
