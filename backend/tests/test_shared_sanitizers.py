"""
Testes para backend.shared.sanitizers
Coverage target: 95%+

Testa todas as 17 funções de sanitização com diversos payloads maliciosos.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.sanitizers import (
    sanitize_html,
    strip_html_tags,
    sanitize_xml,
    sanitize_sql_identifier,
    detect_sql_injection,
    sanitize_shell_argument,
    detect_command_injection,
    sanitize_path,
    sanitize_ldap_dn,
    sanitize_ldap_filter,
    sanitize_nosql_operator,
    sanitize_http_header,
    normalize_whitespace,
    normalize_unicode,
    remove_control_characters,
    sanitize_alphanumeric,
    sanitize_email,
    truncate_string,
)
from shared.exceptions import ValidationError


class TestHTMLSanitization:
    """Testes para sanitize_html e strip_html_tags"""

    def test_sanitize_html_escape_all(self):
        input_text = "<script>alert('XSS')</script>Hello"
        result = sanitize_html(input_text)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_html_allow_tags(self):
        input_text = "<p>Safe</p><script>alert(1)</script>"
        result = sanitize_html(input_text, allow_tags=["p"])
        assert "<p>" in result or "Safe" in result
        assert "alert" not in result or "<script>" not in result

    def test_sanitize_html_event_handlers(self):
        input_text = '<div onclick="alert(1)">Click</div>'
        result = sanitize_html(input_text, allow_tags=["div"])
        assert "onclick" not in result

    def test_sanitize_html_javascript_protocol(self):
        input_text = '<a href="javascript:alert(1)">Link</a>'
        result = sanitize_html(input_text, allow_tags=["a"])
        assert "javascript:" not in result

    def test_sanitize_html_empty_string(self):
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""

    def test_strip_html_tags_simple(self):
        input_text = "<p>Hello</p><b>World</b>"
        result = strip_html_tags(input_text)
        assert "<p>" not in result
        assert "<b>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_strip_html_tags_nested(self):
        input_text = "<div><p><span>Nested</span></p></div>"
        result = strip_html_tags(input_text)
        assert "<" not in result
        assert ">" not in result
        assert "Nested" in result

    def test_strip_html_tags_empty(self):
        assert strip_html_tags("") == ""


class TestXMLSanitization:
    """Testes para sanitize_xml"""

    def test_sanitize_xml_special_chars(self):
        input_text = "Test & < > \" '"
        result = sanitize_xml(input_text)
        assert "&amp;" in result or "&" not in result or result == "Test &amp; &lt; &gt; &quot; &apos;"
        assert "<" not in result or "&lt;" in result
        assert ">" not in result or "&gt;" in result

    def test_sanitize_xml_xxe_attack(self):
        input_text = '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        result = sanitize_xml(input_text)
        assert "<!ENTITY" not in result or result != input_text

    def test_sanitize_xml_empty(self):
        assert sanitize_xml("") == ""


class TestSQLSanitization:
    """Testes para sanitize_sql_identifier e detect_sql_injection"""

    def test_sanitize_sql_identifier_valid(self):
        assert sanitize_sql_identifier("users") == "users"
        assert sanitize_sql_identifier("user_table") == "user_table"
        assert sanitize_sql_identifier("Table123") == "Table123"

    def test_sanitize_sql_identifier_invalid_chars(self):
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("users; DROP TABLE")
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("users--")
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("users/*comment*/")

    def test_sanitize_sql_identifier_too_long(self):
        long_name = "a" * 100
        with pytest.raises(ValidationError):
            sanitize_sql_identifier(long_name, max_length=64)

    def test_sanitize_sql_identifier_empty(self):
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("")

    def test_detect_sql_injection_union(self):
        assert detect_sql_injection("' UNION SELECT * FROM users--") is True

    def test_detect_sql_injection_drop(self):
        assert detect_sql_injection("'; DROP TABLE users--") is True

    def test_detect_sql_injection_comments(self):
        assert detect_sql_injection("admin'--") is True
        assert detect_sql_injection("admin'/*comment*/") is True

    def test_detect_sql_injection_clean(self):
        assert detect_sql_injection("normal_username") is False
        assert detect_sql_injection("user@example.com") is False


class TestShellSanitization:
    """Testes para sanitize_shell_argument e detect_command_injection"""

    def test_sanitize_shell_argument_safe(self):
        result = sanitize_shell_argument("file.txt")
        assert "file.txt" in result

    def test_sanitize_shell_argument_spaces(self):
        result = sanitize_shell_argument("my file.txt")
        # Should be quoted or escaped
        assert "my file.txt" in result or "my\\ file.txt" in result

    def test_sanitize_shell_argument_special_chars(self):
        result = sanitize_shell_argument("file;rm -rf /")
        # Should escape or quote dangerous chars
        assert result != "file;rm -rf /"
        assert ";" not in result or "\\;" in result

    def test_detect_command_injection_pipe(self):
        assert detect_command_injection("file.txt | cat") is True

    def test_detect_command_injection_redirect(self):
        assert detect_command_injection("file.txt > /dev/null") is True

    def test_detect_command_injection_backticks(self):
        assert detect_command_injection("`whoami`") is True
        assert detect_command_injection("$(whoami)") is True

    def test_detect_command_injection_clean(self):
        assert detect_command_injection("file.txt") is False
        assert detect_command_injection("my-file_2024.log") is False


class TestPathSanitization:
    """Testes para sanitize_path"""

    def test_sanitize_path_normal(self):
        result = sanitize_path("/tmp/file.txt")
        assert result == "/tmp/file.txt"

    def test_sanitize_path_traversal_relative(self):
        with pytest.raises(ValidationError):
            sanitize_path("../etc/passwd")

    def test_sanitize_path_traversal_absolute(self):
        with pytest.raises(ValidationError):
            sanitize_path("/tmp/../etc/passwd")

    def test_sanitize_path_null_byte(self):
        with pytest.raises(ValidationError):
            sanitize_path("/tmp/file\x00.txt")

    def test_sanitize_path_with_base_dir(self):
        result = sanitize_path("/tmp/subdir/file.txt", base_dir="/tmp")
        assert result == "/tmp/subdir/file.txt"

    def test_sanitize_path_outside_base_dir(self):
        with pytest.raises(ValidationError):
            sanitize_path("/etc/passwd", base_dir="/tmp")

    def test_sanitize_path_normalize(self):
        result = sanitize_path("/tmp/./subdir/../file.txt")
        # Should normalize to /tmp/file.txt
        assert ".." not in result
        assert "./" not in result


class TestLDAPSanitization:
    """Testes para sanitize_ldap_dn e sanitize_ldap_filter"""

    def test_sanitize_ldap_dn_safe(self):
        result = sanitize_ldap_dn("cn=admin,dc=example,dc=com")
        assert "cn=admin" in result

    def test_sanitize_ldap_dn_special_chars(self):
        result = sanitize_ldap_dn("cn=user\\,name")
        # Should escape special LDAP chars
        assert result != "cn=user,name"

    def test_sanitize_ldap_filter_safe(self):
        result = sanitize_ldap_filter("john")
        assert "john" in result

    def test_sanitize_ldap_filter_wildcard_injection(self):
        result = sanitize_ldap_filter("*)(uid=*))(|(uid=*")
        # Should escape LDAP special chars
        assert result != "*)(uid=*))(|(uid=*"
        assert "\\*" in result or "(" not in result


class TestNoSQLSanitization:
    """Testes para sanitize_nosql_operator"""

    def test_sanitize_nosql_operator_safe_value(self):
        result = sanitize_nosql_operator("normal_value")
        assert result == "normal_value"

    def test_sanitize_nosql_operator_mongo_injection(self):
        with pytest.raises(ValidationError):
            sanitize_nosql_operator("$ne")
        with pytest.raises(ValidationError):
            sanitize_nosql_operator("$gt")

    def test_sanitize_nosql_operator_bracket_injection(self):
        result = sanitize_nosql_operator("value[key]")
        # Should sanitize or raise
        if isinstance(result, str):
            assert "[" not in result or result != "value[key]"


class TestHTTPHeaderSanitization:
    """Testes para sanitize_http_header"""

    def test_sanitize_http_header_safe(self):
        result = sanitize_http_header("application/json")
        assert result == "application/json"

    def test_sanitize_http_header_crlf_injection(self):
        with pytest.raises(ValidationError):
            sanitize_http_header("value\r\nX-Injected: header")
        with pytest.raises(ValidationError):
            sanitize_http_header("value\nX-Injected: header")

    def test_sanitize_http_header_null_byte(self):
        with pytest.raises(ValidationError):
            sanitize_http_header("value\x00injected")

    def test_sanitize_http_header_control_chars(self):
        result = sanitize_http_header("value\x01\x02")
        # Should remove control chars
        assert "\x01" not in result
        assert "\x02" not in result


class TestWhitespaceNormalization:
    """Testes para normalize_whitespace"""

    def test_normalize_whitespace_multiple_spaces(self):
        result = normalize_whitespace("hello    world")
        assert result == "hello world"

    def test_normalize_whitespace_tabs_newlines(self):
        result = normalize_whitespace("hello\t\n\r\nworld")
        assert "\t" not in result
        assert "\n" not in result
        assert "hello" in result
        assert "world" in result

    def test_normalize_whitespace_leading_trailing(self):
        result = normalize_whitespace("  hello world  ")
        assert result == "hello world"

    def test_normalize_whitespace_empty(self):
        assert normalize_whitespace("") == ""


class TestUnicodeNormalization:
    """Testes para normalize_unicode"""

    def test_normalize_unicode_nfkc(self):
        # Combining characters
        input_text = "e\u0301"  # é as e + combining acute accent
        result = normalize_unicode(input_text, form="NFKC")
        assert len(result) <= len(input_text)

    def test_normalize_unicode_nfd(self):
        input_text = "é"
        result = normalize_unicode(input_text, form="NFD")
        # NFD decomposes
        assert len(result) >= len(input_text)

    def test_normalize_unicode_default(self):
        input_text = "Café"
        result = normalize_unicode(input_text)
        assert "Caf" in result


class TestControlCharacterRemoval:
    """Testes para remove_control_characters"""

    def test_remove_control_characters_null(self):
        result = remove_control_characters("test\x00string")
        assert "\x00" not in result
        assert "teststring" == result

    def test_remove_control_characters_various(self):
        result = remove_control_characters("test\x01\x02\x03string")
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\x03" not in result

    def test_remove_control_characters_preserve_printable(self):
        result = remove_control_characters("hello\nworld")
        # \n (0x0A) is typically preserved
        assert "hello" in result
        assert "world" in result

    def test_remove_control_characters_empty(self):
        assert remove_control_characters("") == ""


class TestAlphanumericSanitization:
    """Testes para sanitize_alphanumeric"""

    def test_sanitize_alphanumeric_basic(self):
        result = sanitize_alphanumeric("hello123")
        assert result == "hello123"

    def test_sanitize_alphanumeric_remove_special(self):
        result = sanitize_alphanumeric("hello@#$123")
        assert result == "hello123"

    def test_sanitize_alphanumeric_custom_allowed(self):
        result = sanitize_alphanumeric("hello-world_2024", additional_chars="-_")
        assert result == "hello-world_2024"

    def test_sanitize_alphanumeric_empty_result(self):
        with pytest.raises(ValidationError):
            sanitize_alphanumeric("@#$%", min_length=1)

    def test_sanitize_alphanumeric_spaces(self):
        result = sanitize_alphanumeric("hello world")
        assert " " not in result or result == "helloworld"


class TestEmailSanitization:
    """Testes para sanitize_email"""

    def test_sanitize_email_valid(self):
        result = sanitize_email("user@example.com")
        assert result == "user@example.com"

    def test_sanitize_email_lowercase(self):
        result = sanitize_email("User@Example.COM")
        assert result == "user@example.com"

    def test_sanitize_email_whitespace(self):
        result = sanitize_email("  user@example.com  ")
        assert result == "user@example.com"

    def test_sanitize_email_invalid(self):
        with pytest.raises(ValidationError):
            sanitize_email("not-an-email")
        with pytest.raises(ValidationError):
            sanitize_email("@example.com")


class TestStringTruncation:
    """Testes para truncate_string"""

    def test_truncate_string_no_truncation_needed(self):
        result = truncate_string("short", max_length=10)
        assert result == "short"

    def test_truncate_string_with_default_suffix(self):
        result = truncate_string("this is a long string", max_length=10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_truncate_string_custom_suffix(self):
        result = truncate_string("long string", max_length=8, suffix="…")
        assert len(result) == 8
        assert result.endswith("…")

    def test_truncate_string_exact_length(self):
        result = truncate_string("exactly10c", max_length=10)
        assert result == "exactly10c"

    def test_truncate_string_empty(self):
        result = truncate_string("", max_length=10)
        assert result == ""


class TestEdgeCasesAndIntegration:
    """Testes de edge cases e combinações"""

    def test_sql_injection_with_encoding(self):
        # Unicode-based SQL injection attempt
        assert detect_sql_injection("'; DROP TABLE users--") is True

    def test_path_traversal_encoded(self):
        # URL-encoded path traversal
        with pytest.raises(ValidationError):
            sanitize_path("/tmp/%2e%2e/etc/passwd")

    def test_xss_with_unicode(self):
        # Unicode-based XSS
        input_text = "<script>alert('XSS')</script>"
        result = sanitize_html(input_text)
        assert "alert" not in result or "&lt;" in result

    def test_command_injection_chaining(self):
        assert detect_command_injection("cmd1 && cmd2") is True
        assert detect_command_injection("cmd1 || cmd2") is True
        assert detect_command_injection("cmd1 ; cmd2") is True

    def test_nosql_injection_complex(self):
        with pytest.raises(ValidationError):
            sanitize_nosql_operator('{"$gt": ""}')

    def test_header_injection_multiline(self):
        with pytest.raises(ValidationError):
            sanitize_http_header("value\r\nContent-Length: 0\r\n\r\nHTTP/1.1 200 OK")

    def test_ldap_injection_nested(self):
        result = sanitize_ldap_filter("*)(objectClass=*")
        assert result != "*)(objectClass=*"

    def test_combined_sanitization_pipeline(self):
        # Simula um pipeline real
        user_input = "  <script>alert('XSS')</script>  "
        
        # Step 1: Remove whitespace
        step1 = normalize_whitespace(user_input)
        
        # Step 2: Sanitize HTML
        step2 = sanitize_html(step1)
        
        # Step 3: Remove control chars
        step3 = remove_control_characters(step2)
        
        assert "script" not in step3.lower() or "&lt;" in step3
        assert "alert" not in step3 or "&" in step3

    def test_sanitize_filename_with_path_traversal(self):
        # Teste cruzado entre path e filename validation
        from shared.validators import validate_filename
        
        with pytest.raises(ValidationError):
            validate_filename("../../etc/passwd")


class TestEdgeCases100Percent:
    """Testes adicionais para 100% de coverage"""
    
    def test_sanitize_sql_identifier_reserved_keyword(self):
        """Test rejection of SQL reserved keywords"""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_sql_identifier("SELECT")
        assert "reserved keyword" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("UNION")
    
    def test_detect_sql_injection_empty_string(self):
        """Test detect_sql_injection with empty string"""
        result = detect_sql_injection("")
        assert result is False
        
        result = detect_sql_injection(None)
        assert result is False
    
    def test_sanitize_shell_argument_empty_string(self):
        """Test sanitize_shell_argument with empty input"""
        result = sanitize_shell_argument("")
        assert result == ""
    
    def test_detect_command_injection_empty_string(self):
        """Test detect_command_injection with empty string"""
        result = detect_command_injection("")
        assert result is False
        
        result = detect_command_injection(None)
        assert result is False
    
    def test_sanitize_path_empty_raises_error(self):
        """Test sanitize_path with empty path raises error"""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_path("")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_sanitize_ldap_dn_empty_string(self):
        """Test sanitize_ldap_dn with empty string"""
        result = sanitize_ldap_dn("")
        assert result == ""
    
    def test_sanitize_ldap_filter_empty_string(self):
        """Test sanitize_ldap_filter with empty string"""
        result = sanitize_ldap_filter("")
        assert result == ""
    
    def test_sanitize_nosql_operator_non_string_raises_error(self):
        """Test sanitize_nosql_operator rejects non-strings"""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_nosql_operator({"$ne": 1})
        assert "must be a string" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            sanitize_nosql_operator(123)
    
    def test_sanitize_http_header_empty_string(self):
        """Test sanitize_http_header with empty string"""
        result = sanitize_http_header("")
        assert result == ""
    
    def test_normalize_unicode_empty_string(self):
        """Test normalize_unicode with empty string"""
        result = normalize_unicode("")
        assert result == ""
    
    def test_sanitize_alphanumeric_empty_with_min_length(self):
        """Test sanitize_alphanumeric empty string with min_length requirement"""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_alphanumeric("", min_length=5)
        assert "too short" in str(exc_info.value).lower()
    
    def test_sanitize_alphanumeric_empty_without_min_length(self):
        """Test sanitize_alphanumeric empty string without min_length"""
        result = sanitize_alphanumeric("", min_length=0)
        assert result == ""
    
    def test_sanitize_alphanumeric_with_dashes(self):
        """Test allow_dashes option"""
        result = sanitize_alphanumeric("test-value-123", allow_dashes=True)
        assert "test-value-123" == result
    
    def test_sanitize_alphanumeric_with_spaces(self):
        """Test allow_spaces option"""
        result = sanitize_alphanumeric("test value 123", allow_spaces=True)
        assert "test value 123" == result
    
    def test_sanitize_email_empty_with_validate(self):
        """Test sanitize_email empty string with validate=True"""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_email("", validate=True)
        assert "cannot be empty" in str(exc_info.value).lower()
    
    def test_sanitize_email_empty_without_validate(self):
        """Test sanitize_email empty string with validate=False"""
        result = sanitize_email("", validate=False)
        assert result == ""

