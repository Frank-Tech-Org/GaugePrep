import re

import pytest
from django.test import RequestFactory, override_settings

from modules.identity import throttle
from modules.identity.services import normalize_email


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("203.0.113.7", "203.0.113.7"),
        ("::ffff:203.0.113.7", "203.0.113.7"),
        ("::FFFF:203.0.113.7", "203.0.113.7"),
        ("2001:db8:1:2:aaaa:bbbb:cccc:dddd", "2001:db8:1:2::/64"),
        ("2001:db8:1:2::1", "2001:db8:1:2::/64"),
        ("2001:db8:1:3::1", "2001:db8:1:3::/64"),
        ("fe80::1%eth0", "fe80::/64"),
        (" 2001:DB8:1:2::9 ", "2001:db8:1:2::/64"),
        ("not-an-address", "not-an-address"),
    ],
)
def test_addresses_are_grouped_by_ipv4_or_ipv6_64(raw: str, expected: str) -> None:
    assert throttle.normalize_address(raw) == expected


def test_two_addresses_in_one_64_share_a_key_and_another_64_does_not() -> None:
    first = throttle.normalize_address("2001:db8:1:2::1")
    second = throttle.normalize_address("2001:db8:1:2:ffff::7")
    other = throttle.normalize_address("2001:db8:1:3::1")
    limit = throttle.LOGIN_FAILURES
    assert throttle.key_for(limit, first) == throttle.key_for(limit, second)
    assert throttle.key_for(limit, first) != throttle.key_for(limit, other)


def test_a_mapped_address_shares_the_key_of_its_ipv4_address() -> None:
    limit = throttle.LOGIN_FAILURES
    mapped = throttle.normalize_address("::ffff:198.51.100.9")
    plain = throttle.normalize_address("198.51.100.9")
    assert throttle.key_for(limit, mapped) == throttle.key_for(limit, plain)


@pytest.mark.parametrize(
    "raw", ["Ada@Example.com", "  ada@example.com ", "ADA@EXAMPLE.COM\t"]
)
def test_email_variants_share_one_key(raw: str) -> None:
    limit = throttle.LOGIN_EMAIL_FAILURES
    reference = throttle.key_for(limit, normalize_email("ada@example.com"))
    assert throttle.key_for(limit, normalize_email(raw)) == reference


def test_scopes_do_not_share_keys() -> None:
    assert throttle.key_for(throttle.LOGIN_FAILURES, "x") != throttle.key_for(
        throttle.SIGNUPS, "x"
    )


def test_keys_fit_the_column() -> None:
    key = throttle.key_for(throttle.LOGIN_EMAIL_FAILURES, "ada@example.com")
    assert re.fullmatch(r"[0-9a-f]{64}", key)


def test_keys_change_with_the_secret() -> None:
    before = throttle.key_for(throttle.LOGIN_FAILURES, "203.0.113.7")
    with override_settings(THROTTLE_KEY_SECRET="another-secret"):
        after = throttle.key_for(throttle.LOGIN_FAILURES, "203.0.113.7")
    assert before != after


def test_client_address_is_normalised_behind_the_proxy() -> None:
    request = RequestFactory().get(
        "/", HTTP_X_FORWARDED_FOR="1.1.1.1, ::ffff:203.0.113.7"
    )
    with override_settings(SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https")):
        assert throttle.client_address(request) == "203.0.113.7"


def test_client_address_uses_the_peer_without_a_proxy() -> None:
    request = RequestFactory().get("/", REMOTE_ADDR="2001:db8:9:9::5")
    assert throttle.client_address(request) == "2001:db8:9:9::/64"
