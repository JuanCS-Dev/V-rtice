"""
Testes para backend.shared.validators
Coverage target: 95%+

Testa todas as 21 funções de validação com casos válidos, inválidos e edge cases.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.shared.validators import (
    validate_ipv4,
    validate_ipv6,
    validate_ip_address,
    validate_cidr,
    is_private_ip,
    is_public_ip,
    validate_domain,
    validate_url,
    validate_md5,
    validate_sha1,
    validate_sha256,
    validate_sha512,
    validate_hash,
    validate_email,
    validate_username,
    validate_port,
    validate_file_path,
    validate_filename,
    validate_ioc,
    validate_string_length,
    validate_list_length,
)
from backend.shared.exceptions import ValidationError


class TestIPv4Validation:
    """Testes para validate_ipv4"""

    def test_valid_ipv4(self):
        assert validate_ipv4("192.168.1.1") == "192.168.1.1"
        assert validate_ipv4("8.8.8.8") == "8.8.8.8"
        assert validate_ipv4("0.0.0.0") == "0.0.0.0"
        assert validate_ipv4("255.255.255.255") == "255.255.255.255"

    def test_invalid_ipv4(self):
        with pytest.raises(ValidationError):
            validate_ipv4("256.0.0.1")
        with pytest.raises(ValidationError):
            validate_ipv4("192.168.1")
        with pytest.raises(ValidationError):
            validate_ipv4("192.168.1.1.1")
        with pytest.raises(ValidationError):
            validate_ipv4("not-an-ip")
        with pytest.raises(ValidationError):
            validate_ipv4("")


class TestIPv6Validation:
    """Testes para validate_ipv6"""

    def test_valid_ipv6(self):
        assert validate_ipv6("2001:db8::1") == "2001:db8::1"
        assert validate_ipv6("::1") == "::1"
        assert validate_ipv6("fe80::1") == "fe80::1"
        assert validate_ipv6("2001:0db8:0000:0000:0000:0000:0000:0001") == "2001:db8::1"

    def test_invalid_ipv6(self):
        with pytest.raises(ValidationError):
            validate_ipv6("gggg::1")
        with pytest.raises(ValidationError):
            validate_ipv6("192.168.1.1")
        with pytest.raises(ValidationError):
            validate_ipv6("")


class TestIPAddressValidation:
    """Testes para validate_ip_address (auto-detect)"""

    def test_auto_detect_ipv4(self):
        assert validate_ip_address("192.168.1.1") == "192.168.1.1"

    def test_auto_detect_ipv6(self):
        assert validate_ip_address("::1") == "::1"

    def test_force_version_4(self):
        assert validate_ip_address("8.8.8.8", version=4) == "8.8.8.8"
        with pytest.raises(ValidationError):
            validate_ip_address("::1", version=4)

    def test_force_version_6(self):
        assert validate_ip_address("::1", version=6) == "::1"
        with pytest.raises(ValidationError):
            validate_ip_address("8.8.8.8", version=6)

    def test_invalid_ip(self):
        with pytest.raises(ValidationError):
            validate_ip_address("not-an-ip")


class TestCIDRValidation:
    """Testes para validate_cidr"""

    def test_valid_cidr_v4(self):
        assert validate_cidr("192.168.1.0/24") == "192.168.1.0/24"
        assert validate_cidr("10.0.0.0/8") == "10.0.0.0/8"

    def test_valid_cidr_v6(self):
        assert validate_cidr("2001:db8::/32") == "2001:db8::/32"

    def test_valid_cidr_with_version_param(self):
        # Force IPv4
        assert validate_cidr("192.168.1.0/24", version=4) == "192.168.1.0/24"
        # Force IPv6
        assert validate_cidr("2001:db8::/32", version=6) == "2001:db8::/32"

    def test_invalid_cidr(self):
        with pytest.raises(ValidationError):
            validate_cidr("192.168.1.0/33")  # Invalid prefix
        with pytest.raises(ValidationError):
            validate_cidr("not-a-cidr/24")  # Invalid IP


class TestPrivatePublicIP:
    """Testes para is_private_ip e is_public_ip"""

    def test_private_ipv4(self):
        assert is_private_ip("192.168.1.1") is True
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("127.0.0.1") is True

    def test_public_ipv4(self):
        assert is_public_ip("8.8.8.8") is True
        assert is_public_ip("1.1.1.1") is True

    def test_private_ipv6(self):
        assert is_private_ip("::1") is True
        assert is_private_ip("fe80::1") is True

    def test_public_ipv6(self):
        assert is_public_ip("2001:4860:4860::8888") is True


class TestDomainValidation:
    """Testes para validate_domain"""

    def test_valid_domain(self):
        assert validate_domain("example.com") == "example.com"
        assert validate_domain("sub.example.com") == "sub.example.com"
        assert validate_domain("test-site.co.uk") == "test-site.co.uk"

    def test_invalid_domain(self):
        with pytest.raises(ValidationError):
            validate_domain("")
        with pytest.raises(ValidationError):
            validate_domain("a" * 300)
        with pytest.raises(ValidationError):
            validate_domain("-invalid.com")
        with pytest.raises(ValidationError):
            validate_domain("invalid-.com")


class TestURLValidation:
    """Testes para validate_url"""

    def test_valid_http_url(self):
        result = validate_url("http://example.com")
        assert result == "http://example.com"

    def test_valid_https_url(self):
        result = validate_url("https://example.com/path?query=1")
        assert result == "https://example.com/path?query=1"

    def test_custom_scheme(self):
        result = validate_url("ftp://files.example.com", allowed_schemes=["ftp"])
        assert result == "ftp://files.example.com"

    def test_invalid_scheme(self):
        with pytest.raises(ValidationError):
            validate_url("javascript:alert(1)")
        with pytest.raises(ValidationError):
            validate_url("ftp://example.com", allowed_schemes=["http", "https"])

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            validate_url("not a url")
        with pytest.raises(ValidationError):
            validate_url("")


class TestHashValidation:
    """Testes para validate_md5, sha1, sha256, sha512, validate_hash"""

    def test_valid_md5(self):
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        assert validate_md5(md5) == md5.lower()

    def test_invalid_md5(self):
        with pytest.raises(ValidationError):
            validate_md5("invalid")
        with pytest.raises(ValidationError):
            validate_md5("d41d8cd98f00b204e9800998ecf8427")  # too short

    def test_valid_sha1(self):
        sha1 = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        assert validate_sha1(sha1) == sha1.lower()

    def test_invalid_sha1(self):
        with pytest.raises(ValidationError):
            validate_sha1("invalid")

    def test_valid_sha256(self):
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert validate_sha256(sha256) == sha256.lower()

    def test_invalid_sha256(self):
        with pytest.raises(ValidationError):
            validate_sha256("invalid")

    def test_valid_sha512(self):
        sha512 = "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        assert validate_sha512(sha512) == sha512.lower()

    def test_invalid_sha512(self):
        with pytest.raises(ValidationError):
            validate_sha512("invalid")

    def test_validate_hash_auto_detect(self):
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert validate_hash(md5) == md5
        assert validate_hash(sha256) == sha256

    def test_validate_hash_explicit_type(self):
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        assert validate_hash(md5, hash_type="md5") == md5

    def test_validate_hash_wrong_type(self):
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        with pytest.raises(ValidationError):
            validate_hash(md5, hash_type="sha256")

    def test_validate_hash_invalid(self):
        with pytest.raises(ValidationError):
            validate_hash("not-a-hash")


class TestEmailValidation:
    """Testes para validate_email"""

    def test_valid_email(self):
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("test.user+tag@example.co.uk") == "test.user+tag@example.co.uk"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            validate_email("invalid")
        with pytest.raises(ValidationError):
            validate_email("@example.com")
        with pytest.raises(ValidationError):
            validate_email("user@")
        with pytest.raises(ValidationError):
            validate_email("")


class TestUsernameValidation:
    """Testes para validate_username"""

    def test_valid_username(self):
        assert validate_username("user123") == "user123"
        assert validate_username("test_user") == "test_user"
        assert validate_username("user-name") == "user-name"

    def test_invalid_username_too_short(self):
        with pytest.raises(ValidationError):
            validate_username("ab")

    def test_invalid_username_too_long(self):
        with pytest.raises(ValidationError):
            validate_username("a" * 50, max_length=32)

    def test_invalid_username_chars(self):
        with pytest.raises(ValidationError):
            validate_username("user@name")
        with pytest.raises(ValidationError):
            validate_username("user name")

    def test_custom_length(self):
        assert validate_username("test", min_length=4, max_length=10) == "test"
        with pytest.raises(ValidationError):
            validate_username("tes", min_length=4)


class TestPortValidation:
    """Testes para validate_port"""

    def test_valid_port_int(self):
        assert validate_port(80) == 80
        assert validate_port(443) == 443
        assert validate_port(65535) == 65535

    def test_valid_port_string(self):
        assert validate_port("8080") == 8080
        assert validate_port("443") == 443

    def test_invalid_port_out_of_range(self):
        with pytest.raises(ValidationError):
            validate_port(0)
        with pytest.raises(ValidationError):
            validate_port(65536)
        with pytest.raises(ValidationError):
            validate_port(-1)

    def test_invalid_port_format(self):
        with pytest.raises(ValidationError):
            validate_port("invalid")
        with pytest.raises(ValidationError):
            validate_port("80.5")


class TestFilePathValidation:
    """Testes para validate_file_path"""

    def test_valid_file_path(self):
        result = validate_file_path("/tmp/test.txt")
        assert result == "/tmp/test.txt"

    def test_path_traversal_detection(self):
        with pytest.raises(ValidationError):
            validate_file_path("../etc/passwd")
        with pytest.raises(ValidationError):
            validate_file_path("/tmp/../etc/passwd")

    def test_allowed_extensions(self):
        result = validate_file_path("/tmp/test.txt", allowed_extensions=[".txt", ".log"])
        assert result == "/tmp/test.txt"
        
        with pytest.raises(ValidationError):
            validate_file_path("/tmp/test.exe", allowed_extensions=[".txt", ".log"])

    def test_absolute_path_control(self):
        # Allow absolute (default)
        result = validate_file_path("/tmp/test.txt", allow_absolute=True)
        assert result == "/tmp/test.txt"
        
        # Disallow absolute
        with pytest.raises(ValidationError):
            validate_file_path("/tmp/test.txt", allow_absolute=False)


class TestFilenameValidation:
    """Testes para validate_filename"""

    def test_valid_filename(self):
        assert validate_filename("document.pdf") == "document.pdf"
        assert validate_filename("report_2024.xlsx") == "report_2024.xlsx"

    def test_invalid_chars(self):
        with pytest.raises(ValidationError):
            validate_filename("file/name.txt")
        with pytest.raises(ValidationError):
            validate_filename("file:name.txt")

    def test_max_length(self):
        long_name = "a" * 300 + ".txt"
        with pytest.raises(ValidationError):
            validate_filename(long_name, max_length=255)

    def test_custom_pattern(self):
        # Only allow lowercase letters
        result = validate_filename("test", allowed_chars_pattern=r"^[a-z]+$")
        assert result == "test"
        
        with pytest.raises(ValidationError):
            validate_filename("Test123", allowed_chars_pattern=r"^[a-z]+$")


class TestIOCValidation:
    """Testes para validate_ioc (Indicator of Compromise)"""

    def test_valid_ip_ioc(self):
        assert validate_ioc("192.168.1.1", "ip") == "192.168.1.1"

    def test_valid_domain_ioc(self):
        assert validate_ioc("malicious.com", "domain") == "malicious.com"

    def test_valid_url_ioc(self):
        assert validate_ioc("http://malware.site/payload", "url") == "http://malware.site/payload"

    def test_valid_hash_ioc(self):
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        assert validate_ioc(md5, "hash") == md5

    def test_invalid_ioc_type(self):
        with pytest.raises(ValidationError):
            validate_ioc("test", "unknown_type")

    def test_invalid_ioc_format(self):
        with pytest.raises(ValidationError):
            validate_ioc("not-an-ip", "ip")


class TestStringLengthValidation:
    """Testes para validate_string_length"""

    def test_valid_length(self):
        result = validate_string_length("test", min_length=1, max_length=10)
        assert result == "test"

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_string_length("a", min_length=5)

    def test_too_long(self):
        with pytest.raises(ValidationError):
            validate_string_length("a" * 100, max_length=50)

    def test_empty_string(self):
        with pytest.raises(ValidationError):
            validate_string_length("", min_length=1)


class TestListLengthValidation:
    """Testes para validate_list_length"""

    def test_valid_list_length(self):
        result = validate_list_length([1, 2, 3], min_items=1, max_items=5)
        assert result == [1, 2, 3]

    def test_list_too_short(self):
        with pytest.raises(ValidationError):
            validate_list_length([], min_items=1)

    def test_list_too_long(self):
        with pytest.raises(ValidationError):
            validate_list_length([1, 2, 3, 4, 5], max_items=3)

    def test_no_limits(self):
        result = validate_list_length([1, 2, 3])
        assert result == [1, 2, 3]


class TestEdgeCases:
    """Testes de edge cases e integrações"""

    def test_ipv6_in_url(self):
        result = validate_url("http://[2001:db8::1]:8080/path")
        assert "2001:db8::1" in result

    def test_case_insensitive_hash(self):
        md5_upper = "D41D8CD98F00B204E9800998ECF8427E"
        result = validate_md5(md5_upper)
        assert result == md5_upper.lower()

    def test_domain_with_numbers(self):
        result = validate_domain("123example.com")
        assert result == "123example.com"

    def test_cidr_edge_cases(self):
        # Valid edge cases
        assert validate_cidr("0.0.0.0/0") == "0.0.0.0/0"
        assert validate_cidr("255.255.255.255/32") == "255.255.255.255/32"
