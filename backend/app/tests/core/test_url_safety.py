import pytest

from app.core.url_safety import UnsafeURLError, assert_public_url, assert_public_url_async


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://127.1.2.3:8080/admin",
    "http://10.0.0.1/",
    "http://172.16.0.1/",
    "http://192.168.1.1/",
    "http://169.254.169.254/latest/meta-data/",
    "http://0.0.0.0/",
    "http://100.64.0.1/",  # carrier-grade NAT, not globally routable
    "http://224.0.0.1/",
    "http://240.0.0.1/",
    "http://[::1]/",
    "http://[::]/",
    "http://[fe80::1]/",
    "http://[fc00::1]/",
    "http://[fd12:3456:789a::1]/",
    "http://[ff02::1]/",
    "http://[::ffff:127.0.0.1]/",
    "http://[::ffff:169.254.169.254]/",
    "http://[::ffff:10.0.0.1]/",
    "http://[64:ff9b::a9fe:a9fe]/",  # NAT64 of 169.254.169.254
])
def test_rejects_non_public_ip_literals(url):
    with pytest.raises(UnsafeURLError):
        assert_public_url(url)


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "ftp://example.com/",
    "gopher://example.com/",
    "javascript:alert(1)",
    "",
    "http://",
    "not-a-url",
])
def test_rejects_bad_schemes_and_missing_host(url):
    with pytest.raises(UnsafeURLError):
        assert_public_url(url)


@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.1.2.3", "192.168.0.10", "169.254.169.254", "::1", "fe80::1", "::ffff:127.0.0.1",
])
def test_rejects_hostnames_resolving_to_non_public_addresses(fake_dns, address):
    fake_dns["internal.example.com"] = [address]
    with pytest.raises(UnsafeURLError):
        assert_public_url("https://internal.example.com/health")


def test_rejects_when_any_resolved_address_is_private(fake_dns):
    fake_dns["mixed.example.com"] = ["93.184.216.34", "10.0.0.1"]
    with pytest.raises(UnsafeURLError):
        assert_public_url("https://mixed.example.com/")


def test_rejects_unresolvable_hostname(fake_dns):
    fake_dns["does-not-exist.example"] = []
    with pytest.raises(UnsafeURLError, match="resolve"):
        assert_public_url("https://does-not-exist.example/")


@pytest.mark.parametrize("url", [
    "https://example.com/",
    "http://example.com:8080/status?x=1",
    "https://hooks.slack.com/services/T000/B000/XXXX",
    "http://93.184.216.34/",
    "http://[2606:2800:220:1:248:1893:25c8:1946]/",
    "HTTPS://Example.COM/",
])
def test_accepts_public_http_urls(url):
    assert_public_url(url)


def test_accepts_hostname_resolving_to_public_ipv6(fake_dns):
    fake_dns["v6.example.com"] = ["2606:2800:220:1:248:1893:25c8:1946"]
    assert_public_url("https://v6.example.com/")


@pytest.mark.asyncio
async def test_async_variant_rejects_private_address(fake_dns):
    fake_dns["internal.example.com"] = ["10.0.0.1"]
    with pytest.raises(UnsafeURLError):
        await assert_public_url_async("https://internal.example.com/")


@pytest.mark.asyncio
async def test_async_variant_accepts_public_address():
    await assert_public_url_async("https://example.com/")
