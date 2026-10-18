"""Protection SSRF : vérifie qu'une URL pointe vers une adresse publique avant que le serveur ne la contacte."""
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"http", "https"}
DEFAULT_PORTS = {"http": 80, "https": 443}
NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


class UnsafeURLError(ValueError):
    """Raised when a URL uses a forbidden scheme or resolves to a non-public address."""


def _embedded_ipv4(ip: IPAddress) -> ipaddress.IPv4Address | None:
    """Return the IPv4 address hidden inside an IPv6 one (mapped, NAT64, 6to4, Teredo)."""
    if ip.version != 6:
        return None
    if ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    if ip in NAT64_PREFIX:
        return ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    if ip.sixtofour is not None:
        return ip.sixtofour
    if ip.teredo is not None:
        return ip.teredo[1]
    return None


def is_public_ip(ip: IPAddress) -> bool:
    embedded = _embedded_ipv4(ip)
    if embedded is not None:
        # ::ffff:a.b.c.d is just an IPv4 address: judge it as such.
        if ip.ipv4_mapped is not None:
            return is_public_ip(embedded)
        if not is_public_ip(embedded):
            return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
        or not ip.is_global
    )


def _resolve(host: str, port: int) -> list[IPAddress]:
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as e:
        raise UnsafeURLError(f"Could not resolve host '{host}'") from e

    addresses = []
    for _family, _type, _proto, _canonname, sockaddr in infos:
        # Les adresses IPv6 link-local peuvent avoir un scope id ("fe80::1%eth0")
        addresses.append(ipaddress.ip_address(str(sockaddr[0]).split("%", 1)[0]))
    if not addresses:
        raise UnsafeURLError(f"Could not resolve host '{host}'")
    return addresses


def assert_public_url(url: str) -> None:
    """Raise UnsafeURLError unless `url` is http(s) and every address its host resolves to is public."""
    try:
        parts = urlsplit(str(url).strip())
        port = parts.port
    except ValueError as e:
        raise UnsafeURLError("Malformed URL") from e

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"URL scheme '{scheme}' is not allowed (use http or https)")

    host = parts.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    for ip in _resolve(host, port or DEFAULT_PORTS[scheme]):
        if not is_public_ip(ip):
            raise UnsafeURLError(
                f"URL host '{host}' resolves to {ip}, a private or reserved address that is not allowed"
            )


async def assert_public_url_async(url: str) -> None:
    """Same as assert_public_url, without blocking the event loop on DNS resolution."""
    await asyncio.to_thread(assert_public_url, url)
