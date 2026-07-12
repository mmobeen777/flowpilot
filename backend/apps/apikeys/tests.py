from django.test import SimpleTestCase
from rest_framework import serializers

from .models import APIKey
from .api.serializers import validate_ip_entries


class IsIPAllowedTests(SimpleTestCase):
    """Pure-logic tests for APIKey.is_ip_allowed (no DB access)."""

    def _key(self, allowed_ips):
        return APIKey(allowed_ips=allowed_ips)

    def test_empty_allowlist_permits_any_ip(self):
        key = self._key([])
        self.assertTrue(key.is_ip_allowed("203.0.113.7"))
        self.assertTrue(key.is_ip_allowed("2001:db8::1"))

    def test_exact_ipv4_match(self):
        key = self._key(["203.0.113.7"])
        self.assertTrue(key.is_ip_allowed("203.0.113.7"))
        self.assertFalse(key.is_ip_allowed("203.0.113.8"))

    def test_cidr_range_match(self):
        key = self._key(["203.0.113.0/24"])
        self.assertTrue(key.is_ip_allowed("203.0.113.200"))
        self.assertFalse(key.is_ip_allowed("203.0.114.1"))

    def test_ipv6_cidr_match(self):
        key = self._key(["2001:db8::/32"])
        self.assertTrue(key.is_ip_allowed("2001:db8::abcd"))
        self.assertFalse(key.is_ip_allowed("2001:dead::1"))

    def test_multiple_entries(self):
        key = self._key(["10.0.0.0/8", "203.0.113.7"])
        self.assertTrue(key.is_ip_allowed("10.4.5.6"))
        self.assertTrue(key.is_ip_allowed("203.0.113.7"))
        self.assertFalse(key.is_ip_allowed("192.168.0.1"))

    def test_missing_ip_is_rejected_when_restricted(self):
        key = self._key(["203.0.113.0/24"])
        self.assertFalse(key.is_ip_allowed(None))
        self.assertFalse(key.is_ip_allowed(""))

    def test_malformed_client_ip_is_rejected(self):
        key = self._key(["203.0.113.0/24"])
        self.assertFalse(key.is_ip_allowed("not-an-ip"))

    def test_malformed_allowlist_entry_does_not_fail_open(self):
        key = self._key(["garbage", "203.0.113.0/24"])
        self.assertTrue(key.is_ip_allowed("203.0.113.9"))
        self.assertFalse(key.is_ip_allowed("8.8.8.8"))


class ValidateIPEntriesTests(SimpleTestCase):

    def test_valid_entries_are_normalised(self):
        self.assertEqual(
            validate_ip_entries(["203.0.113.7", " 10.0.0.0/8 "]),
            ["203.0.113.7", "10.0.0.0/8"],
        )

    def test_none_and_empty_become_empty_list(self):
        self.assertEqual(validate_ip_entries(None), [])
        self.assertEqual(validate_ip_entries(""), [])

    def test_invalid_ip_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_ip_entries(["999.0.0.1"])

    def test_non_string_entry_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_ip_entries([123])

    def test_non_list_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_ip_entries("203.0.113.7")
