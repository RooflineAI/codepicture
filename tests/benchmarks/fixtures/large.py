"""HTTP client library with connection pooling and retry logic."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

T = TypeVar("T")


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass(frozen=True)
class HttpHeader:
    name: str
    value: str

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


@dataclass
class HttpRequest:
    method: HttpMethod
    url: str
    headers: list[HttpHeader] = field(default_factory=list)
    body: bytes | None = None
    timeout: float = 30.0

    def add_header(self, name: str, value: str) -> None:
        self.headers.append(HttpHeader(name=name, value=value))

    @property
    def host(self) -> str:
        parsed = urlparse(self.url)
        return parsed.hostname or ""

    @property
    def path(self) -> str:
        parsed = urlparse(self.url)
        return parsed.path or "/"


@dataclass
class HttpResponse:
    status_code: int
    headers: list[HttpHeader] = field(default_factory=list)
    body: bytes = b""

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    def get_header(self, name: str) -> str | None:
        for header in self.headers:
            if header.name.lower() == name.lower():
                return header.value
        return None


class Transport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...
    def close(self) -> None: ...


class RetryStrategy(ABC):
    @abstractmethod
    def should_retry(
        self, attempt: int, response: HttpResponse | None, error: Exception | None
    ) -> bool: ...

    @abstractmethod
    def get_delay(self, attempt: int) -> float: ...


class ExponentialBackoff(RetryStrategy):
    def __init__(
        self, max_retries: int = 3, base_delay: float = 0.5, max_delay: float = 30.0
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def should_retry(
        self, attempt: int, response: HttpResponse | None, error: Exception | None
    ) -> bool:
        if attempt >= self.max_retries:
            return False
        if error is not None:
            return True
        if response and response.status_code in (429, 500, 502, 503, 504):
            return True
        return False

    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (2**attempt)
        return min(delay, self.max_delay)


@dataclass
class ConnectionPool:
    max_connections: int = 10
    _active: dict[str, list[Transport]] = field(default_factory=dict)

    def acquire(self, host: str) -> Transport | None:
        connections = self._active.get(host, [])
        if connections:
            return connections.pop()
        return None

    def release(self, host: str, transport: Transport) -> None:
        if host not in self._active:
            self._active[host] = []
        if len(self._active[host]) < self.max_connections:
            self._active[host].append(transport)
        else:
            transport.close()

    def close_all(self) -> None:
        for host, connections in self._active.items():
            for conn in connections:
                conn.close()
        self._active.clear()


class ResponseIterator(Generic[T]):
    """Paginated response iterator."""

    def __init__(self, items: list[T], page_size: int = 20) -> None:
        self._items = items
        self._page_size = page_size
        self._offset = 0

    def __iter__(self) -> Iterator[list[T]]:
        return self

    def __next__(self) -> list[T]:
        if self._offset >= len(self._items):
            raise StopIteration
        page = self._items[self._offset : self._offset + self._page_size]
        self._offset += self._page_size
        return page

    @property
    def total(self) -> int:
        return len(self._items)

    @property
    def remaining(self) -> int:
        return max(0, len(self._items) - self._offset)


class HttpClient:
    """HTTP client with connection pooling and configurable retry."""

    def __init__(
        self,
        base_url: str = "",
        retry_strategy: RetryStrategy | None = None,
        default_headers: dict[str, str] | None = None,
        pool_size: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.retry_strategy = retry_strategy or ExponentialBackoff()
        self.default_headers = default_headers or {}
        self._pool = ConnectionPool(max_connections=pool_size)
        self._interceptors: list[RequestInterceptor] = []

    def add_interceptor(self, interceptor: RequestInterceptor) -> None:
        self._interceptors.append(interceptor)

    def _build_request(
        self,
        method: HttpMethod,
        path: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        timeout: float = 30.0,
    ) -> HttpRequest:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        request = HttpRequest(method=method, url=url, body=body, timeout=timeout)

        for name, value in self.default_headers.items():
            request.add_header(name, value)

        if headers:
            for name, value in headers.items():
                request.add_header(name, value)

        for interceptor in self._interceptors:
            request = interceptor.before_request(request)

        return request

    def get(self, path: str, **kwargs: Any) -> HttpResponse:
        request = self._build_request(HttpMethod.GET, path, **kwargs)
        return self._execute(request)

    def post(self, path: str, **kwargs: Any) -> HttpResponse:
        request = self._build_request(HttpMethod.POST, path, **kwargs)
        return self._execute(request)

    def _execute(self, request: HttpRequest) -> HttpResponse:
        attempt = 0
        last_error: Exception | None = None

        while True:
            try:
                transport = self._pool.acquire(request.host)
                if transport is None:
                    logger.debug("No pooled connection for %s", request.host)
                    raise ConnectionError(f"No transport for {request.host}")

                response = transport.send(request)
                self._pool.release(request.host, transport)

                if not self.retry_strategy.should_retry(attempt, response, None):
                    return response

            except Exception as exc:
                last_error = exc
                if not self.retry_strategy.should_retry(attempt, None, exc):
                    raise

            delay = self.retry_strategy.get_delay(attempt)
            logger.info("Retry %d after %.1fs", attempt + 1, delay)
            time.sleep(delay)
            attempt += 1

    def close(self) -> None:
        self._pool.close_all()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class RequestInterceptor(ABC):
    @abstractmethod
    def before_request(self, request: HttpRequest) -> HttpRequest: ...


class AuthInterceptor(RequestInterceptor):
    def __init__(self, token: str) -> None:
        self._token = token

    def before_request(self, request: HttpRequest) -> HttpRequest:
        request.add_header("Authorization", f"Bearer {self._token}")
        return request
