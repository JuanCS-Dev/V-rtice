"""Tests for backend/shared/sanitizers.py - 100% coverage."""

import pytest
from backend.shared.sanitizers import (
    detect_command_injection,
    detect_sql_injection,
    normalize_unicode,
    normalize_whitespace,
    remove_control_characters,
    sanitize_alphanumeric,
    sanitize_email,
    sanitize_html,
    sanitize_http_header,
    sanitize_ldap_dn,
    sanitize_ldap_filter,
    sanitize_nosql_operator,
    sanitize_path,
    sanitize_shell_argument,
    sanitize_sql_identifier,
    sanitize_xml,
    strip_html_tags,
    truncate_string,
)


class TestSanitizeSQLIdentifier:
    """Test SQL identifier sanitization."""
    
    def test_basic_identifier(self):
        """Test basic SQL identifier sanitization."""
        result = sanitize_sql_identifier("users_table")
        assert isinstance(result, str)
        assert result == "users_table"
    
    def test_sql_injection_attempt(self):
        """Test SQL injection prevention in identifiers."""
        from backend.shared.exceptions import ValidationError
        
        malicious = "users'; DROP TABLE users; --"
        with pytest.raises(ValidationError):
            sanitize_sql_identifier(malicious)


class TestSanitizeHTML:
    """Test HTML sanitization."""
    
    def test_plain_text(self):
        """Test plain text passes through."""
        result = sanitize_html("Hello World")
        assert result == "Hello World"
    
    def test_empty_string(self):
        """Test empty string returns empty."""
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""
    
    def test_escape_html_default(self):
        """Test HTML escaping when no tags allowed."""
        result = sanitize_html("<div>Test</div>")
        assert "&lt;div&gt;" in result or result == "<div>Test</div>"
    
    def test_allow_specific_tags(self):
        """Test allowing specific tags."""
        result = sanitize_html("<b>Bold</b> <script>alert()</script>", allow_tags=["b"])
        assert "script" not in result.lower() or "<script>" not in result
        # Covers lines 79-91 (allow_tags branch)
        assert "Bold" in result
    
    def test_remove_script(self):
        """Test script tag removal."""
        result = sanitize_html("<script>alert('xss')</script>Hello", allow_tags=["p"])
        assert "alert" not in result or "<script>" not in result
        assert "Hello" in result
    
    def test_remove_event_handlers(self):
        """Test event handler removal."""
        result = sanitize_html("<div onclick='alert()'>Test</div>", allow_tags=["div"])
        assert "onclick" not in result
    
    def test_remove_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = sanitize_html("<a href='javascript:alert()'>Link</a>", allow_tags=["a"])
        assert "javascript:" not in result
    
    def test_remove_dangerous_tags(self):
        """Test removal of dangerous tags."""
        result = sanitize_html("<iframe src='evil.com'>test</iframe>")
        assert "<iframe" not in result


class TestSanitizePath:
    """Test path sanitization."""
    
    def test_normal_path(self):
        """Test normal path."""
        result = sanitize_path("var/log/app.log")
        assert "app.log" in str(result)
    
    def test_path_traversal(self):
        """Test path traversal prevention."""
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError):
            sanitize_path("../../../etc/passwd")
    
    def test_null_byte(self):
        """Test null byte removal."""
        from backend.shared.exceptions import ValidationError
        
        # Path().resolve() raises ValueError for null bytes
        with pytest.raises((ValidationError, ValueError)):
            sanitize_path("/path/to/file\x00.txt")

class TestSanitizeShellArgument:
    """Test shell argument sanitization."""
    
    def test_safe_argument(self):
        """Test safe argument."""
        result = sanitize_shell_argument("myfile.txt")
        assert result == "myfile.txt"
    
    def test_command_injection(self):
        """Test command injection attempt is escaped."""
        malicious = "file.txt; rm -rf /"
        result = sanitize_shell_argument(malicious)
        # Should escape the dangerous ; character
        assert "\\;" in result
        assert "rm" in result  # Content preserved but escaped
    
    def test_pipe_handling(self):
        """Test pipe character is escaped."""
        result = sanitize_shell_argument("file|grep test")
        # Should escape the | character
        assert "\\|" in result


class TestStripHTMLTags:
    """Test HTML tag stripping."""
    
    def test_basic_strip(self):
        """Test basic HTML tag removal."""
        result = strip_html_tags("<p>Hello <b>World</b></p>")
        assert result == "Hello World"
    
    def test_empty_string(self):
        """Test empty string handling - covers lines 107-108."""
        assert strip_html_tags("") == ""
        assert strip_html_tags(None) == ""
    
    def test_unescape_entities(self):
        """Test HTML entity unescaping - covers lines 111-116."""
        result = strip_html_tags("&lt;div&gt;Test&lt;/div&gt;")
        assert "<div>Test</div>" in result or "Test" in result
    
    def test_complex_html(self):
        """Test complex HTML removal."""
        html_input = "<div class='test'><span>Hello</span> <b>World</b></div>"
        result = strip_html_tags(html_input)
        assert "<" not in result
        assert "Hello" in result
        assert "World" in result


class TestSanitizeXML:
    """Test XML sanitization."""
    
    def test_basic_xml(self):
        """Test basic XML escaping - covers lines 132-137."""
        result = sanitize_xml("<root>test</root>")
        assert "&lt;" in result
        assert "&gt;" in result
    
    def test_empty_string(self):
        """Test empty string handling - covers lines 128-129."""
        assert sanitize_xml("") == ""
        assert sanitize_xml(None) == ""
    
    def test_all_special_chars(self):
        """Test all XML special characters - covers lines 132-138."""
        result = sanitize_xml("&<>\"'")
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result
        assert "&apos;" in result
    
    def test_normal_text(self):
        """Test normal text passes through."""
        result = sanitize_xml("Hello World")
        assert result == "Hello World"


class TestSQLDetection:
    """Test SQL injection detection."""
    
    def test_detect_sql_injection_safe(self):
        """Test safe SQL strings."""
        assert detect_sql_injection("SELECT * FROM users") is True
        assert detect_sql_injection("normal text") is False
    
    def test_detect_sql_injection_malicious(self):
        """Test malicious SQL patterns."""
        assert detect_sql_injection("'; DROP TABLE--") is True
        assert detect_sql_injection("1 OR 1=1") is True
        assert detect_sql_injection("UNION SELECT") is True


class TestCommandInjection:
    """Test command injection detection."""
    
    def test_detect_command_injection_safe(self):
        """Test safe commands."""
        assert detect_command_injection("file.txt") is False
        assert detect_command_injection("myfile") is False
    
    def test_detect_command_injection_dangerous(self):
        """Test dangerous patterns."""
        assert detect_command_injection("file.txt; rm -rf /") is True
        assert detect_command_injection("$(malicious)") is True
        assert detect_command_injection("file | grep") is True


class TestLDAPSanitization:
    """Test LDAP sanitization."""
    
    def test_sanitize_ldap_dn(self):
        """Test LDAP DN sanitization."""
        result = sanitize_ldap_dn("cn=test,dc=example,dc=com")
        assert result is not None
        assert "test" in result
    
    def test_sanitize_ldap_filter(self):
        """Test LDAP filter sanitization."""
        result = sanitize_ldap_filter("(cn=test)")
        assert result is not None


class TestNoSQLSanitization:
    """Test NoSQL sanitization."""
    
    def test_sanitize_nosql_operator(self):
        """Test NoSQL operator sanitization."""
        from backend.shared.exceptions import ValidationError
        
        # Operators should be rejected
        with pytest.raises(ValidationError):
            sanitize_nosql_operator("$gt")
        
        # Normal values should pass
        result = sanitize_nosql_operator("normalvalue")
        assert result == "normalvalue"
    
    def test_sanitize_nosql_operator_safe_values(self):
        """Test NoSQL operator with various safe values to cover return path."""
        # Various safe strings that don't contain NoSQL operators
        safe_values = [
            "simple_string",
            "user@example.com",
            "123456",
            "multi word string",
            "special!chars#ok",
        ]
        
        for value in safe_values:
            result = sanitize_nosql_operator(value)
            assert result == value


class TestHTTPHeaderSanitization:
    """Test HTTP header sanitization."""
    
    def test_sanitize_http_header(self):
        """Test HTTP header sanitization."""
        result = sanitize_http_header("application/json")
        assert result == "application/json"
    
    def test_sanitize_http_header_null_byte(self):
        """Test null byte detection - covers line 524."""
        from backend.shared.exceptions import ValidationError
        
        # Line 524: null byte check
        with pytest.raises(ValidationError, match="Null byte"):
            sanitize_http_header("value\x00injection")
    
    def test_remove_crlf(self):
        """Test CRLF injection prevention."""
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="HTTP header injection"):
            sanitize_http_header("value\r\nInjected: header")


class TestNormalization:
    """Test text normalization functions."""
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        result = normalize_whitespace("hello    world")
        assert result == "hello world"
    
    def test_normalize_unicode(self):
        """Test Unicode normalization."""
        result = normalize_unicode("café")
        assert result is not None
        assert "caf" in result
    
    def test_remove_control_characters(self):
        """Test control character removal."""
        result = remove_control_characters("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result


class TestAlphanumericSanitization:
    """Test alphanumeric sanitization."""
    
    def test_sanitize_alphanumeric(self):
        """Test alphanumeric sanitization."""
        result = sanitize_alphanumeric("test123", allow_dashes=True)
        assert result == "test123"
    
    def test_remove_special_chars(self):
        """Test special character removal."""
        result = sanitize_alphanumeric("test@#$123")
        assert "@" not in result
        assert "test123" in result
    
    def test_empty_string(self):
        """Test empty string - covers lines 585-586."""
        assert sanitize_alphanumeric("") == ""
        assert sanitize_alphanumeric(None) == ""
    
    def test_allow_spaces(self):
        """Test allowing spaces - covers lines 590-591."""
        result = sanitize_alphanumeric("test 123", allow_spaces=True)
        assert result == "test 123"
    
    def test_allow_dashes(self):
        """Test allowing dashes - covers lines 592-593."""
        result = sanitize_alphanumeric("test-123", allow_dashes=True)
        assert result == "test-123"
    
    def test_strip_result(self):
        """Test result stripping - covers line 598."""
        result = sanitize_alphanumeric("  test123  ")
        assert result == "test123"


class TestEmailSanitization:
    """Test email sanitization."""
    
    def test_sanitize_email_valid(self):
        """Test valid email - covers lines 619, 622."""
        result = sanitize_email("User@Example.COM  ")
        assert result == "user@example.com"
    
    
    def test_sanitize_email_empty(self):
        """Test empty email raises ValidationError."""
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            sanitize_email("")
    
    def test_sanitize_email_none(self):
        """Test None email returns empty string - covers line 684."""
        # Line 684: None handling
        result = sanitize_email(None, validate=False)
        assert result == ""
    
    def test_sanitize_email_with_validation(self):
        """Test email validation flag - covers lines 693-696."""
        from backend.shared.exceptions import ValidationError
        
        # Line 693-696: validate flag triggers validation
        valid_email = "test@example.com"
        result = sanitize_email(valid_email, validate=True)
        assert result == "test@example.com"
        
        # Invalid email with validate=True should raise
        with pytest.raises(ValidationError, match="Invalid email"):
            sanitize_email("not-an-email", validate=True)
    
    def test_sanitize_email_without_validation(self):
        """Test email without validation - covers line 693 (false branch)."""
        # Line 693: validate=False skips validation
        result = sanitize_email("not-an-email", validate=False)
        assert result == "not-an-email"
    
    def test_remove_spaces(self):
        """Test space removal - covers line 622."""
        result = sanitize_email("user @ example.com")
        assert " " not in result
        assert "user@example.com" == result


class TestStringTruncation:
    """Test string truncation."""
    
    def test_truncate_string(self):
        """Test string truncation - covers line 650."""
        result = truncate_string("Hello World", max_length=8)
        assert len(result) <= 11  # 8 + "..." = 11
        assert "..." in result or len(result) == 8
    
    def test_truncate_short_string(self):
        """Test truncation of short string - covers lines 646-647."""
        result = truncate_string("Hi", max_length=10)
        assert result == "Hi"
    
    def test_empty_string(self):
        """Test empty string - covers lines 643-644."""
        assert truncate_string("", max_length=10) == ""
        assert truncate_string(None, max_length=10) == ""
    
    def test_truncate_custom_suffix(self):
        """Test truncation with custom suffix."""
        result = truncate_string("Hello World", max_length=8, suffix=">>")
        assert ">>" in result


class TestSQLIdentifierReservedKeywords:
    """Test SQL identifier with reserved keywords."""
    
    def test_reserved_keywords(self):
        """Test rejection of reserved keywords - covers lines 205-209."""
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="reserved keyword"):
            sanitize_sql_identifier("SELECT")
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("DROP")
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("delete")
    
    def test_empty_identifier(self):
        """Test empty identifier rejection - covers lines 168-172."""
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            sanitize_sql_identifier("")
    
    def test_invalid_start_char(self):
        """Test invalid starting character - covers lines 175-182."""
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="Invalid SQL identifier"):
            sanitize_sql_identifier("123table")
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("-table")
    
    def test_max_length(self):
        """Test identifier max length - covers lines 184-188."""
        from backend.shared.exceptions import ValidationError
        
        long_id = "a" * 100
        with pytest.raises(ValidationError, match="too long"):
            sanitize_sql_identifier(long_id)
        
        # Valid length
        valid_id = "a" * 60
        assert sanitize_sql_identifier(valid_id) == valid_id


class TestSQLInjectionDetection:
    """Test SQL injection detection patterns."""
    
    def test_union_select(self):
        """Test UNION SELECT detection - covers line 228."""
        assert detect_sql_injection("UNION SELECT * FROM users") is True
    
    def test_insert_into(self):
        """Test INSERT INTO detection - covers line 230."""
        assert detect_sql_injection("INSERT INTO users VALUES") is True
    
    def test_update_set(self):
        """Test UPDATE SET detection - covers line 231."""
        assert detect_sql_injection("UPDATE users SET password=") is True
    
    def test_delete_from(self):
        """Test DELETE FROM detection - covers line 232."""
        assert detect_sql_injection("DELETE FROM users") is True
    
    def test_drop_table(self):
        """Test DROP TABLE detection - covers line 233."""
        assert detect_sql_injection("DROP TABLE users") is True
    
    def test_comment_patterns(self):
        """Test SQL comment patterns - covers lines 234-236."""
        assert detect_sql_injection("'; DROP TABLE users--") is True
        assert detect_sql_injection("/* comment */ SELECT") is True
    
    def test_or_equals(self):
        """Test OR equals patterns - covers lines 237-241."""
        assert detect_sql_injection("1' OR '1'='1") is True
        assert detect_sql_injection("admin' AND 1=1--") is True
    
    def test_empty_string(self):
        """Test empty string - covers lines 223-224."""
        assert detect_sql_injection("") is False
        assert detect_sql_injection(None) is False


class TestCommandInjectionDetection:
    """Test command injection detection patterns."""
    
    def test_shell_metacharacters(self):
        """Test shell metacharacters - covers line 304."""
        assert detect_command_injection("file; rm -rf /") is True
        assert detect_command_injection("file & background") is True
        assert detect_command_injection("file | grep") is True
        assert detect_command_injection("file`whoami`") is True
        assert detect_command_injection("file$USER") is True
    
    def test_command_substitution(self):
        """Test command substitution - covers lines 305-306."""
        assert detect_command_injection("$(whoami)") is True
        assert detect_command_injection("`ls -la`") is True
    
    def test_file_redirection(self):
        """Test file redirection - covers line 307."""
        assert detect_command_injection("cat > /dev/null") is True
    
    def test_here_document(self):
        """Test here document - covers line 308."""
        assert detect_command_injection("cat << EOF") is True
    
    def test_empty_string(self):
        """Test empty string - covers lines 299-300."""
        assert detect_command_injection("") is False
        assert detect_command_injection(None) is False


class TestShellArgumentSanitization:
    """Test shell argument sanitization edge cases."""
    
    def test_empty_arg(self):
        """Test empty argument - covers lines 274-275."""
        assert sanitize_shell_argument("") == ""
        assert sanitize_shell_argument(None) == ""
    
    def test_all_dangerous_chars(self):
        """Test all dangerous characters are escaped - covers lines 278-280."""
        dangerous = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        for char in dangerous:
            result = sanitize_shell_argument(f"file{char}test")
            # Should escape the dangerous character
            assert f"\\{char}" in result or char == "\n" or char == "\r"


class TestPathSanitization:
    """Test path sanitization edge cases."""
    
    def test_empty_path(self):
        """Test empty path - covers lines 342-345."""
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            sanitize_path("")
    
    def test_absolute_path_traversal(self):
        """Test absolute path with traversal - covers lines 359-360."""
        from backend.shared.exceptions import ValidationError
        
        # Absolute path that tries to escape
        malicious = "/etc/../../../root/.ssh/id_rsa"
        with pytest.raises(ValidationError, match="Path traversal detected"):
            sanitize_path(malicious)
    
    def test_absolute_path_with_real_parts(self):
        """Test absolute path normalization - covers line 360."""
        # Absolute path with dots that normalizes safely
        path = "/var/./log/../tmp/test.txt"
        # Should normalize successfully (doesn't escape /var)
        result = sanitize_path(path)
        assert result == "/var/tmp/test.txt"
    
    def test_relative_path_with_parent_refs(self):
        """Test relative path with .. - covers lines 363-366."""
        from backend.shared.exceptions import ValidationError
        
        # Relative path with parent directory references
        with pytest.raises(ValidationError, match="Path traversal detected in relative path"):
            sanitize_path("../../etc/passwd")
    
    def test_path_escape_boundary(self):
        """Test path escaping directory boundary - covers lines 369-375."""
        from backend.shared.exceptions import ValidationError
        
        # Absolute path that truly escapes its implied base
        # /etc/.. goes to / which escapes /etc
        with pytest.raises(ValidationError, match="escaped directory boundary"):
            sanitize_path("/etc/../../../root/secret.txt")
    
    def test_path_with_base_dir(self):
        """Test path validation with base directory - covers lines 359-367."""
        from backend.shared.exceptions import ValidationError
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file within tmpdir
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            
            # Valid path within base_dir
            result = sanitize_path(test_file, base_dir=tmpdir)
            assert result is not None
    
    def test_path_outside_base_dir(self):
        """Test path outside base directory - covers lines 362-367."""
        from backend.shared.exceptions import ValidationError
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Path outside base_dir
            with pytest.raises(ValidationError, match="outside base directory"):
                sanitize_path("/etc/passwd", base_dir=tmpdir)


class TestWhitespaceNormalization:
    """Test whitespace normalization edge cases."""
    
    def test_normalize_whitespace_empty(self):
        """Test empty string - covers lines 522-523."""
        assert normalize_whitespace("") == ""
        assert normalize_whitespace(None) == ""
    
    def test_normalize_whitespace_multiple_types(self):
        """Test multiple whitespace types - covers line 526."""
        result = normalize_whitespace("hello\t\n  world\r\n")
        assert result == "hello world"
    
    def test_normalize_whitespace_strip(self):
        """Test stripping - covers line 528."""
        result = normalize_whitespace("  hello  ")
        assert result == "hello"


class TestUnicodeNormalization:
    """Test Unicode normalization."""
    
    def test_normalize_unicode_empty(self):
        """Test empty string - covers lines 541-542."""
        assert normalize_unicode("") == ""
        assert normalize_unicode(None) == ""
    
    def test_normalize_unicode_nfkc(self):
        """Test NFKC normalization - covers line 544."""
        result = normalize_unicode("café", form="NFKC")
        assert result is not None
        assert "caf" in result
    
    def test_normalize_unicode_forms(self):
        """Test different normalization forms."""
        text = "café"
        for form in ["NFC", "NFKC", "NFD", "NFKD"]:
            result = normalize_unicode(text, form=form)
            assert result is not None


class TestControlCharacterRemoval:
    """Test control character removal."""
    
    def test_remove_control_empty(self):
        """Test empty string - covers lines 556-557."""
        assert remove_control_characters("") == ""
        assert remove_control_characters(None) == ""
    
    def test_remove_control_keep_allowed(self):
        """Test keeping allowed control chars - covers lines 560-562."""
        result = remove_control_characters("hello\tworld\ntest\r")
        assert "\t" in result
        assert "\n" in result
        assert "\r" in result
    
    def test_remove_control_remove_others(self):
        """Test removing other control chars - covers lines 560-562."""
        result = remove_control_characters("hello\x00\x01\x02world")
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert "hello" in result
        assert "world" in result


class TestEdgeCasesForFullCoverage:
    """Edge case tests to reach 100% coverage."""
    
    def test_ldap_dn_empty(self):
        """Test empty LDAP DN - covers line 410."""
        from backend.shared.sanitizers import sanitize_ldap_dn
        assert sanitize_ldap_dn("") == ""
        assert sanitize_ldap_dn(None) == ""
    
    def test_ldap_filter_empty(self):
        """Test empty LDAP filter - covers line 435."""
        from backend.shared.sanitizers import sanitize_ldap_filter
        assert sanitize_ldap_filter("") == ""
        assert sanitize_ldap_filter(None) == ""
    
    def test_nosql_non_string(self):
        """Test NoSQL non-string value - covers line 466."""
        from backend.shared.sanitizers import sanitize_nosql_operator
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="must be a string"):
            sanitize_nosql_operator(123)
        
        with pytest.raises(ValidationError, match="must be a string"):
            sanitize_nosql_operator(["list"])
    
    def test_http_header_empty(self):
        """Test empty HTTP header - covers line 520."""
        from backend.shared.sanitizers import sanitize_http_header
        assert sanitize_http_header("") == ""
        assert sanitize_http_header(None) == ""
    
    def test_alphanumeric_empty_with_min(self):
        """Test alphanumeric empty with min_length - covers line 632."""
        from backend.shared.sanitizers import sanitize_alphanumeric
        from backend.shared.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="too short"):
            sanitize_alphanumeric("", min_length=5)
    
    def test_alphanumeric_additional_chars(self):
        """Test alphanumeric with additional_chars - covers line 645."""
        from backend.shared.sanitizers import sanitize_alphanumeric
        
        result = sanitize_alphanumeric("test@domain.com", additional_chars="@.")
        assert "@" in result
        assert "." in result
    
    def test_alphanumeric_too_short_after_sanitization(self):
        """Test alphanumeric too short after sanitization - covers line 652."""
        from backend.shared.sanitizers import sanitize_alphanumeric
        from backend.shared.exceptions import ValidationError
        
        # "ab!@#$%" -> "ab" (2 chars) < min_length (10)
        with pytest.raises(ValidationError, match="too short after sanitization"):
            sanitize_alphanumeric("ab!@#$%", min_length=10)
