#!/usr/bin/env python3
"""
Advanced Migration Script: Frontend API Integration
Handles complex patterns that bash can't easily do
Governed by: Constituição Vértice v2.7
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Tuple

class FrontendMigrator:
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.migrated = 0
        self.skipped = 0
        self.failed = 0
        self.manual_review = []
        
    def find_files_with_localhost(self) -> List[Path]:
        """Find all JS/JSX files with localhost URLs"""
        files = []
        for pattern in ['**/*.js', '**/*.jsx']:
            for file in self.src_dir.glob(pattern):
                if 'node_modules' in str(file):
                    continue
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'localhost:8' in content:
                        files.append(file)
        return files
    
    def add_import_if_needed(self, content: str) -> str:
        """Add apiClient import if not present"""
        if "import { apiClient }" in content or "import apiClient" in content:
            return content
        
        # Find last import line
        import_lines = [i for i, line in enumerate(content.split('\n')) 
                       if line.strip().startswith('import ')]
        
        if import_lines:
            lines = content.split('\n')
            last_import = import_lines[-1]
            lines.insert(last_import + 1, "import { apiClient } from '@/api/client';")
            return '\n'.join(lines)
        
        # No imports found, add at top after comments/docstrings
        lines = content.split('\n')
        insert_pos = 0
        in_comment = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith('/*'):
                in_comment = True
            if in_comment and '*/' in line:
                in_comment = False
                insert_pos = i + 1
                continue
            if not in_comment and line.strip() and not line.strip().startswith('//'):
                insert_pos = i
                break
        
        lines.insert(insert_pos, "import { apiClient } from '@/api/client';")
        lines.insert(insert_pos + 1, "")
        return '\n'.join(lines)
    
    def migrate_simple_get(self, content: str) -> Tuple[str, bool]:
        """Migrate simple GET fetch calls"""
        changed = False
        
        # Pattern: await fetch(`http://localhost:8000/endpoint`)
        pattern1 = r"await fetch\(`http://localhost:8000(/[^`]+)`\)"
        if re.search(pattern1, content):
            content = re.sub(pattern1, r"await apiClient.get('\1')", content)
            changed = True
        
        # Pattern: await fetch('http://localhost:8000/endpoint')
        pattern2 = r"await fetch\('http://localhost:8000(/[^']+)'\)"
        if re.search(pattern2, content):
            content = re.sub(pattern2, r"await apiClient.get('\1')", content)
            changed = True
        
        # Pattern: fetch without await
        pattern3 = r"fetch\(`http://localhost:8000(/[^`]+)`\)"
        if re.search(pattern3, content):
            content = re.sub(pattern3, r"apiClient.get('\1')", content)
            changed = True
        
        return content, changed
    
    def migrate_post_requests(self, content: str) -> Tuple[str, bool]:
        """Migrate POST fetch calls"""
        changed = False
        
        # Pattern: fetch with POST method and body
        # This is complex, using regex with multiline
        pattern = r"await fetch\([`'\"]http://localhost:8000(/[^`'\"]+)[`'\"],\s*\{[^}]*method:\s*['\"]POST['\"][^}]*body:\s*JSON\.stringify\(([^)]+)\)[^}]*\}\)"
        
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if matches:
            for match in reversed(matches):  # Reverse to maintain positions
                endpoint = match.group(1)
                payload = match.group(2).strip()
                replacement = f"await apiClient.post('{endpoint}', {payload})"
                content = content[:match.start()] + replacement + content[match.end():]
                changed = True
        
        return content, changed
    
    def remove_unnecessary_json_parsing(self, content: str) -> Tuple[str, bool]:
        """Remove .json() calls after apiClient (it returns parsed JSON)"""
        changed = False
        
        # Pattern: const x = await apiClient.get(...).then(r => r.json())
        pattern1 = r"(await apiClient\.[a-z]+\([^)]+\))\.then\(\s*r\s*=>\s*r\.json\(\)\s*\)"
        if re.search(pattern1, content):
            content = re.sub(pattern1, r'\1', content)
            changed = True
        
        # Pattern: const x = await apiClient.get(...); const json = await x.json()
        # This is tricky, might need manual review
        
        return content, changed
    
    def migrate_file(self, file_path: Path) -> str:
        """Migrate a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()
            
            content = original
            any_changes = False
            
            # Step 1: Add import
            content = self.add_import_if_needed(content)
            if content != original:
                any_changes = True
            
            # Step 2: Migrate GET requests
            content, changed = self.migrate_simple_get(content)
            if changed:
                any_changes = True
            
            # Step 3: Migrate POST requests
            content, changed = self.migrate_post_requests(content)
            if changed:
                any_changes = True
            
            # Step 4: Clean up JSON parsing
            content, changed = self.remove_unnecessary_json_parsing(content)
            if changed:
                any_changes = True
            
            if any_changes:
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.migrated += 1
                return "✓ MIGRATED"
            else:
                self.skipped += 1
                return "○ SKIPPED"
                
        except Exception as e:
            self.failed += 1
            return f"✗ FAILED: {str(e)}"
    
    def run(self):
        """Run migration on all files"""
        print("════════════════════════════════════════════════════════════════")
        print(" Python Advanced Migration")
        print("════════════════════════════════════════════════════════════════")
        print()
        
        files = self.find_files_with_localhost()
        print(f"Found {len(files)} files to process\n")
        
        for file in files:
            rel_path = file.relative_to(self.src_dir)
            status = self.migrate_file(file)
            print(f"{status} {rel_path}")
        
        print()
        print("════════════════════════════════════════════════════════════════")
        print(" SUMMARY")
        print("════════════════════════════════════════════════════════════════")
        print(f"Migrated: {self.migrated}")
        print(f"Skipped:  {self.skipped}")
        print(f"Failed:   {self.failed}")
        print()
        
        return 0 if self.failed == 0 else 1

if __name__ == '__main__':
    frontend_src = "/home/juan/vertice-dev/frontend/src"
    
    if not os.path.exists(frontend_src):
        print(f"Error: {frontend_src} not found")
        sys.exit(1)
    
    migrator = FrontendMigrator(frontend_src)
    sys.exit(migrator.run())
