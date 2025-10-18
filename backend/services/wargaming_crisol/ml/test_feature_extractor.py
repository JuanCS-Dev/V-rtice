"""
Tests for Patch Feature Extractor.

NO MOCK - Real patches, real feature extraction.
PRODUCTION-READY - Comprehensive edge cases.
"""

from ml.feature_extractor import (
    PatchFeatures,
    PatchFeatureExtractor,
)


class TestPatchFeatures:
    """Test PatchFeatures dataclass"""
    
    def test_to_dict_converts_booleans_to_int(self):
        """Booleans must be int for scikit-learn"""
        features = PatchFeatures(
            lines_added=10,
            lines_removed=5,
            files_modified=2,
            complexity_delta=3.0,
            has_input_validation=True,
            has_sanitization=False,
            has_encoding=True,
            has_parameterization=False,
            cwe_id="CWE-89",
        )
        
        data = features.to_dict()
        
        assert data['has_input_validation'] == 1
        assert data['has_sanitization'] == 0
        assert data['has_encoding'] == 1
        assert data['has_parameterization'] == 0
        assert isinstance(data['has_input_validation'], int)


class TestPatchFeatureExtractor:
    """Test feature extraction from patches"""
    
    def test_extract_basic_metrics(self):
        """Extract lines added/removed/files"""
        patch = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -10,3 +10,5 @@
 def handler():
-    query = f"SELECT * FROM users WHERE id = {user_id}"
+    query = "SELECT * FROM users WHERE id = ?"
+    cursor.execute(query, (user_id,))
"""
        
        features = PatchFeatureExtractor.extract(patch, "CWE-89")
        
        assert features.lines_added == 2
        assert features.lines_removed == 1
        assert features.files_modified == 1
        assert features.cwe_id == "CWE-89"
    
    def test_extract_input_validation_patterns(self):
        """Detect input validation"""
        patch = """diff --git a/app.py b/app.py
+    if not user_input:
+        raise ValueError("Invalid input")
+    if user_input is None:
+        return
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        assert features.has_input_validation is True
    
    def test_extract_sanitization_patterns(self):
        """Detect sanitization"""
        patch = """diff --git a/app.py b/app.py
+    user_input = sanitize(user_input)
+    clean_data = user_input.strip().lower()
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        assert features.has_sanitization is True
    
    def test_extract_encoding_patterns(self):
        """Detect encoding/escaping"""
        patch = """diff --git a/app.py b/app.py
+    from html import escape
+    safe_html = escape(user_input)
+    encoded = urllib.parse.quote(url)
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        assert features.has_encoding is True
    
    def test_extract_parameterization_patterns(self):
        """Detect parameterized queries"""
        patch = """diff --git a/app.py b/app.py
-    query = f"SELECT * FROM users WHERE id = {user_id}"
+    query = "SELECT * FROM users WHERE id = ?"
+    cursor.execute(query, (user_id,))
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        assert features.has_parameterization is True
    
    def test_extract_complexity_delta_positive(self):
        """Complexity increases with added control flow"""
        patch = """diff --git a/app.py b/app.py
+    if user_input:
+        for item in items:
+            while condition:
+                try:
+                    process()
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        # 4 control flow statements added
        assert features.complexity_delta > 0
    
    def test_extract_complexity_delta_negative(self):
        """Complexity decreases when removing control flow"""
        patch = """diff --git a/app.py b/app.py
-    if user_input:
-        for item in items:
-            while condition:
-                pass
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        # 3 control flow statements removed
        assert features.complexity_delta < 0
    
    def test_extract_empty_patch(self):
        """Handle empty patch gracefully"""
        features = PatchFeatureExtractor.extract("", "CWE-79")
        
        assert features.lines_added == 0
        assert features.lines_removed == 0
        assert features.files_modified == 0
        assert features.complexity_delta == 0.0
        assert features.has_input_validation is False
        assert features.cwe_id == "CWE-79"
    
    def test_extract_multiple_files(self):
        """Count multiple files modified"""
        patch = """diff --git a/app.py b/app.py
+    # change 1
diff --git a/utils.py b/utils.py
+    # change 2
diff --git a/models.py b/models.py
+    # change 3
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        assert features.files_modified == 3
    
    def test_extract_comprehensive_security_patch(self):
        """Real-world security patch with multiple patterns"""
        patch = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -15,10 +15,15 @@ def search_users(query):
-    sql = f"SELECT * FROM users WHERE name LIKE '%{query}%'"
-    cursor.execute(sql)
+    # Input validation
+    if not query or len(query) > 100:
+        raise ValueError("Invalid query")
+    
+    # Sanitize input
+    query = query.strip().lower()
+    
+    # Parameterized query
+    sql = "SELECT * FROM users WHERE name LIKE ?"
+    cursor.execute(sql, (f'%{query}%',))
     return cursor.fetchall()
"""
        
        features = PatchFeatureExtractor.extract(patch, "CWE-89")
        
        # All security patterns present
        assert features.has_input_validation is True
        assert features.has_sanitization is True
        assert features.has_parameterization is True
        
        # More lines added than removed (security improvement)
        assert features.lines_added > features.lines_removed
        
        # Complexity increased (added validation logic)
        assert features.complexity_delta > 0
        
        assert features.cwe_id == "CWE-89"


class TestFeatureExtractorEdgeCases:
    """Edge cases and error handling"""
    
    def test_malformed_patch_does_not_crash(self):
        """Handle malformed patches gracefully"""
        patch = "this is not a valid patch\n+++random text"
        
        # Should not raise exception
        features = PatchFeatureExtractor.extract(patch)
        
        assert isinstance(features, PatchFeatures)
    
    def test_patch_with_only_comments(self):
        """Patches with only comments have no security patterns"""
        patch = """diff --git a/app.py b/app.py
+    # TODO: add validation
+    # FIXME: sanitize input
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        # Comments don't trigger patterns
        assert features.has_input_validation is False
        assert features.has_sanitization is False
    
    def test_case_insensitive_pattern_matching(self):
        """Patterns should be case-insensitive"""
        patch = """diff --git a/app.py b/app.py
+    IF NOT user_input:
+        RAISE ValueError("Invalid")
"""
        
        features = PatchFeatureExtractor.extract(patch)
        
        # Should match despite uppercase
        assert features.has_input_validation is True
