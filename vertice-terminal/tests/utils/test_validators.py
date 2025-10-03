
import pytest
from vertice.utils.validators import validate_ip, validate_domain, validate_hash

# Testes para validate_ip
@pytest.mark.parametrize("ip_string, expected", [
    ("8.8.8.8", True),
    ("192.168.1.1", True),
    ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", True), # IPv6
    ("256.0.0.1", False),
    ("not-an-ip", False),
    ("127.0.0.1.1", False),
    ("", False),
])
def test_validate_ip(ip_string, expected):
    assert validate_ip(ip_string) == expected

# Testes para validate_domain
@pytest.mark.parametrize("domain_string, expected", [
    ("google.com", True),
    ("sub.domain.co.uk", True),
    ("a-domain-with-hyphens.net", True),
    ("1.1.1.1", False), # Should not match an IP
    ("-invalid.com", False), # Starts with hyphen
    ("invalid-.com", False), # Ends with hyphen
    ("no_tld", False),
    ("domain..com", False), # Double dots
    ("", False),
])
def test_validate_domain(domain_string, expected):
    assert validate_domain(domain_string) == expected

# Testes para validate_hash
@pytest.mark.parametrize("hash_value, hash_type, expected", [
    # MD5
    ("d41d8cd98f00b204e9800998ecf8427e", "md5", True),
    ("d41d8cd98f00b204e9800998ecf8427", "md5", False), # Too short
    ("d41d8cd98f00b204e9800998ecf8427e1", "md5", False), # Too long
    ("g41d8cd98f00b204e9800998ecf8427e", "md5", False), # Invalid char

    # SHA1
    ("da39a3ee5e6b4b0d3255bfef95601890afd80709", "sha1", True),
    ("da39a3ee5e6b4b0d3255bfef95601890afd8070", "sha1", False), # Too short

    # SHA256
    ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "sha256", True),
    ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85", "sha256", False), # Too short

    # Invalid type
    ("any_string", "sha512", False),
])
def test_validate_hash(hash_value, hash_type, expected):
    assert validate_hash(hash_value, hash_type) == expected
