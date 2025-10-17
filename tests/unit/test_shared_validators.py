"""Tests for backend/shared/validators.py - 95%+ coverage target."""

import pytest
from backend.shared.validators import (
    validate_ip_address,
    validate_ipv4,
    validate_ipv6,
    validate_domain,
    validate_email,
    validate_url,
    validate_port,
    validate_cidr,
    validate_md5,
    validate_sha1,
    validate_sha256,
    validate_sha512,
    validate_hash,
    validate_username,
    validate_file_path,
    validate_filename,
    is_public_ip,
    is_private_ip,
)
from backend.shared.exceptions import ValidationError


class TestValidateIP:
    """Test IP address validation."""
    
    def test_valid_ipv4(self):
        """Test valid IPv4 addresses."""
        assert validate_ipv4("192.168.1.1") == "192.168.1.1"
        assert validate_ipv4("8.8.8.8") == "8.8.8.8"
        assert validate_ipv4("0.0.0.0") == "0.0.0.0"
        assert validate_ipv4("255.255.255.255") == "255.255.255.255"
    
    def test_valid_ipv6(self):
        """Test valid IPv6 addresses."""
        assert validate_ipv6("::1") == "::1"
        assert validate_ipv6("2001:db8::1") == "2001:db8::1"
        assert validate_ipv6("fe80::1") == "fe80::1"
        assert validate_ipv6("2001:0db8:0000:0000:0000:0000:0000:0001") == "2001:db8::1"
    
    def test_invalid_ipv4(self):
        """Test invalid IPv4 addresses."""
        with pytest.raises(ValidationError):
            validate_ipv4("256.1.1.1")
        with pytest.raises(ValidationError):
            validate_ipv4("invalid")
        with pytest.raises(ValidationError):
            validate_ipv4("")
        with pytest.raises(ValidationError):
            validate_ipv4("192.168.1")
        with pytest.raises(ValidationError):
            validate_ipv4("300.300.300.300")
    
    def test_invalid_ipv6(self):
        """Test invalid IPv6 addresses."""
        with pytest.raises(ValidationError):
            validate_ipv6("invalid")
        with pytest.raises(ValidationError):
            validate_ipv6("gggg::1")
        with pytest.raises(ValidationError):
            validate_ipv6("192.168.1.1")
    
    def test_generic_ip_validator_ipv4(self):
        """Test generic IP validator with IPv4."""
        assert validate_ip_address("192.168.1.1") == "192.168.1.1"
        assert validate_ip_address("8.8.8.8") == "8.8.8.8"
        assert validate_ip_address("192.168.1.1", version=4) == "192.168.1.1"
    
    def test_generic_ip_validator_ipv6(self):
        """Test generic IP validator with IPv6."""
        assert validate_ip_address("::1") == "::1"
        assert validate_ip_address("2001:db8::1") == "2001:db8::1"
        assert validate_ip_address("::1", version=6) == "::1"
    
    def test_generic_ip_validator_invalid(self):
        """Test generic IP validator with invalid input."""
        with pytest.raises(ValidationError):
            validate_ip_address("invalid")
        with pytest.raises(ValidationError):
            validate_ip_address("256.1.1.1", version=4)
        with pytest.raises(ValidationError):
            validate_ip_address("192.168.1.1", version=6)
    
    def test_is_public_ip(self):
        """Test public IP detection."""
        assert is_public_ip("8.8.8.8") is True
        assert is_public_ip("1.1.1.1") is True
        assert is_public_ip("192.168.1.1") is False
        assert is_public_ip("10.0.0.1") is False
        assert is_public_ip("127.0.0.1") is False
        assert is_public_ip("invalid") is False
    
    def test_is_private_ip(self):
        """Test private IP detection."""
        assert is_private_ip("192.168.1.1") is True
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("invalid") is False


class TestValidateCIDR:
    """Test CIDR validation."""
    
    def test_valid_cidr_ipv4(self):
        """Test valid IPv4 CIDR notation."""
        assert validate_cidr("192.168.1.0/24") == "192.168.1.0/24"
        assert validate_cidr("10.0.0.0/8") == "10.0.0.0/8"
        assert validate_cidr("172.16.0.0/12") == "172.16.0.0/12"
        assert validate_cidr("192.168.1.0/24", version=4) == "192.168.1.0/24"
    
    def test_valid_cidr_ipv6(self):
        """Test valid IPv6 CIDR notation."""
        result = validate_cidr("2001:db8::/32")
        assert "2001:db8" in result
        result = validate_cidr("2001:db8::/32", version=6)
        assert "2001:db8" in result
    
    def test_invalid_cidr(self):
        """Test invalid CIDR notation."""
        with pytest.raises(ValidationError):
            validate_cidr("invalid/24")
        with pytest.raises(ValidationError):
            validate_cidr("192.168.1.0/33")
        with pytest.raises(ValidationError):
            validate_cidr("")


class TestValidateDomain:
    """Test domain validation."""
    
    def test_valid_domain(self):
        """Test valid domains."""
        assert validate_domain("example.com") == "example.com"
        assert validate_domain("sub.example.com") == "sub.example.com"
        assert validate_domain("test-site.org") == "test-site.org"
        assert validate_domain("my.site.co.uk") == "my.site.co.uk"
        assert validate_domain("EXAMPLE.COM") == "example.com"
    
    def test_invalid_domain(self):
        """Test invalid domains."""
        with pytest.raises(ValidationError):
            validate_domain("")
        with pytest.raises(ValidationError):
            validate_domain("invalid domain")
        with pytest.raises(ValidationError):
            validate_domain("-invalid.com")
        with pytest.raises(ValidationError):
            validate_domain("a" * 300 + ".com")


class TestValidateURL:
    """Test URL validation."""
    
    def test_valid_url_https(self):
        """Test valid HTTPS URLs."""
        assert validate_url("https://example.com") == "https://example.com"
        assert validate_url("https://test.org/path") == "https://test.org/path"
        assert validate_url("https://api.example.com:8080/v1") == "https://api.example.com:8080/v1"
    
    def test_valid_url_http(self):
        """Test valid HTTP URLs."""
        assert validate_url("http://example.com") == "http://example.com"
        assert validate_url("http://test.org/path?query=1") == "http://test.org/path?query=1"
    
    def test_valid_url_custom_scheme(self):
        """Test URL with custom allowed schemes."""
        assert validate_url("ftp://example.com", allowed_schemes=["ftp"]) == "ftp://example.com"
        assert validate_url("ws://example.com", allowed_schemes=["ws", "wss"]) == "ws://example.com"
    
    def test_invalid_url_scheme(self):
        """Test invalid URL schemes."""
        with pytest.raises(ValidationError):
            validate_url("ftp://example.com")
        with pytest.raises(ValidationError):
            validate_url("javascript:alert(1)")
    
    def test_invalid_url_format(self):
        """Test invalid URL formats."""
        with pytest.raises(ValidationError):
            validate_url("not-a-url")
        with pytest.raises(ValidationError):
            validate_url("http://")
        with pytest.raises(ValidationError):
            validate_url("")


class TestValidatePort:
    """Test port validation."""
    
    def test_valid_port(self):
        """Test valid ports."""
        assert validate_port(80) == 80
        assert validate_port(443) == 443
        assert validate_port(8080) == 8080
        assert validate_port(1) == 1
        assert validate_port(65535) == 65535
        assert validate_port(3000) == 3000
    
    def test_invalid_port(self):
        """Test invalid ports."""
        with pytest.raises(ValidationError):
            validate_port(0)
        with pytest.raises(ValidationError):
            validate_port(65536)
        with pytest.raises(ValidationError):
            validate_port(-1)
        with pytest.raises(ValidationError):
            validate_port(100000)


class TestValidateHash:
    """Test hash validation."""
    
    def test_valid_md5(self):
        """Test valid MD5 hash."""
        md5 = "5d41402abc4b2a76b9719d911017c592"
        assert validate_md5(md5) == md5
        assert validate_md5(md5.upper()) == md5
        assert validate_md5("  " + md5 + "  ") == md5
    
    def test_invalid_md5(self):
        """Test invalid MD5 hash."""
        with pytest.raises(ValidationError):
            validate_md5("invalid")
        with pytest.raises(ValidationError):
            validate_md5("5d41402abc4b2a76b9719d911017c59")
        with pytest.raises(ValidationError):
            validate_md5("5d41402abc4b2a76b9719d911017c592z")
    
    def test_valid_sha1(self):
        """Test valid SHA1 hash."""
        sha1 = "2fd4e1c67a2d28fced849ee1bb76e7391b93eb12"
        assert validate_sha1(sha1) == sha1
        assert validate_sha1(sha1.upper()) == sha1
    
    def test_invalid_sha1(self):
        """Test invalid SHA1 hash."""
        with pytest.raises(ValidationError):
            validate_sha1("invalid")
        with pytest.raises(ValidationError):
            validate_sha1("2fd4e1c67a2d28fced849ee1bb76e7391b93eb1")
    
    def test_valid_sha256(self):
        """Test valid SHA256 hash."""
        sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert validate_sha256(sha) == sha
        assert validate_sha256(sha.upper()) == sha
    
    def test_invalid_sha256(self):
        """Test invalid SHA256 hash."""
        with pytest.raises(ValidationError):
            validate_sha256("invalid")
        with pytest.raises(ValidationError):
            validate_sha256("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85")
    
    def test_valid_sha512(self):
        """Test valid SHA512 hash."""
        sha512 = "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        assert validate_sha512(sha512) == sha512
        assert validate_sha512(sha512.upper()) == sha512
    
    def test_invalid_sha512(self):
        """Test invalid SHA512 hash."""
        with pytest.raises(ValidationError):
            validate_sha512("invalid")
        with pytest.raises(ValidationError):
            validate_sha512("cf83e1357eefb8bdf1542850d66d8007")
    
    def test_validate_hash_auto_detect(self):
        """Test automatic hash type detection."""
        md5 = "5d41402abc4b2a76b9719d911017c592"
        sha1 = "2fd4e1c67a2d28fced849ee1bb76e7391b93eb12"
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        sha512 = "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        
        assert validate_hash(md5) == md5
        assert validate_hash(sha1) == sha1
        assert validate_hash(sha256) == sha256
        assert validate_hash(sha512) == sha512
    
    def test_validate_hash_explicit_type(self):
        """Test hash validation with explicit type."""
        md5 = "5d41402abc4b2a76b9719d911017c592"
        assert validate_hash(md5, "md5") == md5
        assert validate_hash(md5, "MD5") == md5
    
    def test_validate_hash_invalid_type(self):
        """Test hash validation with invalid type."""
        with pytest.raises(ValidationError):
            validate_hash("5d41402abc4b2a76b9719d911017c592", "sha3")
    
    def test_validate_hash_invalid_length(self):
        """Test hash validation with invalid length."""
        with pytest.raises(ValidationError):
            validate_hash("invalid")
        with pytest.raises(ValidationError):
            validate_hash("5d41402abc")


class TestValidateEmail:
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("test.user@sub.example.com") == "test.user@sub.example.com"
        assert validate_email("User+Tag@Example.COM") == "user+tag@example.com"
        assert validate_email("  user@example.com  ") == "user@example.com"
    
    def test_invalid_email(self):
        """Test invalid email addresses."""
        with pytest.raises(ValidationError):
            validate_email("invalid")
        with pytest.raises(ValidationError):
            validate_email("@example.com")
        with pytest.raises(ValidationError):
            validate_email("user@")
        with pytest.raises(ValidationError):
            validate_email("")
        with pytest.raises(ValidationError):
            validate_email("user@example")


class TestValidateUsername:
    """Test username validation."""
    
    def test_valid_username(self):
        """Test valid usernames."""
        assert validate_username("user123") == "user123"
        assert validate_username("test_user") == "test_user"
        assert validate_username("user-name") == "user-name"
        assert validate_username("abc") == "abc"
    
    def test_invalid_username_length(self):
        """Test invalid username length."""
        with pytest.raises(ValidationError):
            validate_username("ab")
        with pytest.raises(ValidationError):
            validate_username("a" * 33)
    
    def test_invalid_username_format(self):
        """Test invalid username format."""
        with pytest.raises(ValidationError):
            validate_username("user@name")
        with pytest.raises(ValidationError):
            validate_username("user name")
        with pytest.raises(ValidationError):
            validate_username("")


class TestValidateFilepath:
    """Test filepath validation."""
    
    def test_valid_filepath(self):
        """Test valid filepaths."""
        from backend.shared.validators import validate_file_path
        assert validate_file_path("/var/log/app.log") == "/var/log/app.log"
        assert validate_file_path("/home/user/file.txt") == "/home/user/file.txt"
        assert validate_file_path("relative/path/file.txt") == "relative/path/file.txt"
    
    def test_valid_filepath_with_extension(self):
        """Test filepath with allowed extensions."""
        from backend.shared.validators import validate_file_path
        assert validate_file_path("/var/log/app.log", allowed_extensions=[".log"]) == "/var/log/app.log"
    
    def test_invalid_filepath_traversal(self):
        """Test path traversal detection."""
        from backend.shared.validators import validate_file_path
        with pytest.raises(ValidationError):
            validate_file_path("../etc/passwd")
        with pytest.raises(ValidationError):
            validate_file_path("/var/../../etc/passwd")
        with pytest.raises(ValidationError):
            validate_file_path("/var/log/../../../etc/passwd")
    
    def test_invalid_filepath_absolute(self):
        """Test absolute path rejection when not allowed."""
        from backend.shared.validators import validate_file_path
        with pytest.raises(ValidationError):
            validate_file_path("/var/log/app.log", allow_absolute=False)
    
    def test_invalid_filepath_extension(self):
        """Test invalid extension rejection."""
        from backend.shared.validators import validate_file_path
        with pytest.raises(ValidationError):
            validate_file_path("/var/log/app.log", allowed_extensions=[".txt"])


class TestValidateFilename:
    """Test filename validation."""
    
    def test_valid_filename(self):
        """Test valid filenames."""
        assert validate_filename("file.txt") == "file.txt"
        assert validate_filename("document.pdf") == "document.pdf"
        assert validate_filename("image_2024.jpg") == "image_2024.jpg"
        assert validate_filename("file_name-v1.2.tar.gz") == "file_name-v1.2.tar.gz"
    
    def test_invalid_filename_length(self):
        """Test filename length validation."""
        with pytest.raises(ValidationError):
            validate_filename("a" * 300)
    
    def test_invalid_filename_special(self):
        """Test filename with invalid characters."""
        with pytest.raises(ValidationError):
            validate_filename("file<>.txt")
        with pytest.raises(ValidationError):
            validate_filename("file|name.txt")
    
    def test_invalid_filename_reserved(self):
        """Test reserved Windows filenames."""
        with pytest.raises(ValidationError):
            validate_filename("CON.txt")
        with pytest.raises(ValidationError):
            validate_filename("NUL")
        with pytest.raises(ValidationError):
            validate_filename("LPT1.log")
    
    def test_filename_custom_pattern(self):
        """Test filename with custom pattern - covers line 615."""
        result = validate_filename("file123", allowed_chars_pattern=r"^[a-z0-9]+$")
        assert result == "file123"
        
        with pytest.raises(ValidationError):
            validate_filename("File_123", allowed_chars_pattern=r"^[a-z0-9]+$")


class TestValidateDomainLength:
    """Test domain validation edge cases."""
    
    def test_domain_max_length(self):
        """Test domain max length - covers line 224."""
        long_domain = "subdomain." * 30 + "verylongdomainname.com"
        assert len(long_domain) > 253
        with pytest.raises(ValidationError):
            validate_domain(long_domain)


class TestValidateEmailLength:
    """Test email validation edge cases."""
    
    def test_email_max_length(self):
        """Test email max length - covers line 455."""
        long_email = "a" * 250 + "@test.com"
        assert len(long_email) > 254
        with pytest.raises(ValidationError, match="too long"):
            validate_email(long_email)


class TestValidatePortEdgeCases:
    """Test port validation edge cases."""
    
    def test_port_string_conversion(self):
        """Test port string conversion - covers lines 522-524."""
        assert validate_port("8080") == 8080
        assert validate_port("443") == 443
    
    def test_port_invalid_type(self):
        """Test port invalid type - covers lines 523-527."""
        with pytest.raises(ValidationError, match="Invalid port number"):
            validate_port("invalid")
        with pytest.raises(ValidationError):
            validate_port("abc")
        with pytest.raises(ValidationError):
            validate_port(None)


class TestValidateIOC:
    """Test IOC validation."""
    
    def test_validate_ioc_ip(self):
        """Test IOC validation for IP - covers lines 668-686."""
        from backend.shared.validators import validate_ioc
        
        assert validate_ioc("192.168.1.1", "ip") == "192.168.1.1"
        assert validate_ioc("example.com", "domain") == "example.com"
    
    def test_validate_ioc_hash(self):
        """Test IOC validation for hash - covers lines 668-686."""
        from backend.shared.validators import validate_ioc
        
        md5 = "5d41402abc4b2a76b9719d911017c592"
        assert validate_ioc(md5, "md5") == md5
        assert validate_ioc(md5, "hash") == md5
    
    def test_validate_ioc_unknown_type(self):
        """Test IOC validation with unknown type - covers lines 680-684."""
        from backend.shared.validators import validate_ioc
        
        with pytest.raises(ValidationError, match="Unknown IOC type"):
            validate_ioc("test", "unknown_type")


class TestValidateStringLength:
    """Test string length validation."""
    
    def test_validate_string_length_valid(self):
        """Test string length validation - covers lines 710-724."""
        from backend.shared.validators import validate_string_length
        
        assert validate_string_length("test", min_length=1, max_length=10) == "test"
        assert validate_string_length("hello", min_length=5, max_length=5) == "hello"
    
    def test_validate_string_length_too_short(self):
        """Test string too short - covers lines 710-724."""
        from backend.shared.validators import validate_string_length
        
        with pytest.raises(ValidationError, match="too short"):
            validate_string_length("ab", min_length=3)
    
    def test_validate_string_length_too_long(self):
        """Test string too long - covers lines 710-724."""
        from backend.shared.validators import validate_string_length
        
        with pytest.raises(ValidationError, match="too long"):
            validate_string_length("hello world", max_length=5)


class TestValidateListLength:
    """Test list length validation."""
    
    def test_validate_list_length_valid(self):
        """Test list length validation - covers lines 743-757."""
        from backend.shared.validators import validate_list_length
        
        assert validate_list_length([1, 2, 3], min_items=1, max_items=5) == [1, 2, 3]
        assert validate_list_length([1], min_items=1, max_items=1) == [1]
    
    def test_validate_list_length_too_short(self):
        """Test list too short - covers lines 743-757."""
        from backend.shared.validators import validate_list_length
        
        with pytest.raises(ValidationError):
            validate_list_length([1], min_items=2)
    
    def test_validate_list_length_too_long(self):
        """Test list too long - covers lines 743-757."""
        from backend.shared.validators import validate_list_length
        
        with pytest.raises(ValidationError):
            validate_list_length([1, 2, 3, 4], max_items=3)
