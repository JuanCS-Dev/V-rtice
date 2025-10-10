#!/usr/bin/env python3
"""
Purpose: Automatically fix common broken links after reorganization
Usage: ./fix-broken-links.py [--dry-run]
Author: MAXIMUS Team
Date: 2025-10-10
"""

import re
import sys
from pathlib import Path
from typing import Dict, List

# Mapping of old paths to new paths (from reorganization)
LINK_MAPPINGS = {
    # Phase docs moved to docs/phases/completed/
    'ETHICAL_AI_EXECUTIVE_SUMMARY.md': 'docs/reports/ethical-ai-executive-summary.md',
    'PHASE_0_GOVERNANCE_COMPLETE.md': 'docs/phases/completed/phase-0-governance.md',
    'PHASE_4_1_DP_COMPLETE.md': 'docs/phases/completed/phase-4-1-differential-privacy.md',
    'PHASE_5_HITL_COMPLETE.md': 'docs/phases/completed/phase-5-human-in-the-loop.md',
    
    # Architecture docs
    'ETHICAL_POLICIES.md': 'docs/architecture/ethical-policies.md',
    'API_DOCUMENTATION.md': 'docs/architecture/api-documentation.md',
    
    # Guides
    'DEPENDENCY_GOVERNANCE_FRAMEWORK.md': 'docs/architecture/dependency-governance-framework.md',
    'DEPENDENCY_FRAMEWORK_ROLLOUT_GUIDE.md': 'docs/guides/dependency-framework-rollout.md',
    'DEPENDENCY_FRAMEWORK_COMPLETE_REPORT.md': 'docs/reports/dependency-framework-complete.md',
    'DEPENDENCY_FRAMEWORK_VALIDATION_REPORT.md': 'docs/reports/validations/dependency-framework-validation.md',
}

def fix_file_links(file_path: Path, dry_run: bool = False) -> int:
    """Fix links in a single file. Returns number of fixes."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        fixes = 0
        
        # Fix each mapping
        for old_link, new_link in LINK_MAPPINGS.items():
            # Calculate relative path from file to new location
            source_dir = file_path.parent
            target_path = Path(new_link)
            
            try:
                relative = Path('../' * (len(source_dir.relative_to(Path.cwd()).parts))) / target_path
                relative_str = str(relative).replace('\\', '/')
                
                # Replace direct references
                pattern1 = rf'\[([^\]]+)\]\({re.escape(old_link)}\)'
                replacement1 = rf'[\1]({relative_str})'
                new_content = re.sub(pattern1, replacement1, content)
                
                # Replace ./file references
                pattern2 = rf'\[([^\]]+)\]\(\.\/{re.escape(old_link)}\)'
                replacement2 = rf'[\1]({relative_str})'
                new_content = re.sub(pattern2, replacement2, new_content)
                
                if new_content != content:
                    fixes += (content.count(old_link) - new_content.count(old_link))
                    content = new_content
                    
            except ValueError:
                # Can't make relative path, skip
                continue
        
        if content != original_content and not dry_run:
            file_path.write_text(content, encoding='utf-8')
            
        return fixes
        
    except Exception as e:
        print(f"⚠️  Error fixing {file_path}: {e}")
        return 0

def main():
    dry_run = '--dry-run' in sys.argv
    root = Path.cwd()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           🔧 BROKEN LINKS FIXER - MAXIMUS Vértice        ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    # Find all markdown files
    md_files = []
    md_files.extend(root.glob("docs/**/*.md"))
    md_files.extend(root.glob("*.md"))
    
    print(f"📄 Scanning {len(md_files)} files...\n")
    
    total_fixes = 0
    files_fixed = 0
    
    for md_file in md_files:
        fixes = fix_file_links(md_file, dry_run)
        if fixes > 0:
            files_fixed += 1
            total_fixes += fixes
            relative_path = md_file.relative_to(root)
            status = "Would fix" if dry_run else "Fixed"
            print(f"  ✓ {status} {fixes} link(s) in {relative_path}")
    
    print("\n" + "=" * 70)
    print(f"\n📊 SUMMARY:")
    print(f"  • Files scanned: {len(md_files)}")
    print(f"  • Files modified: {files_fixed}")
    print(f"  • Links fixed: {total_fixes}")
    
    if dry_run and total_fixes > 0:
        print(f"\n💡 Run without --dry-run to apply fixes")
    elif total_fixes > 0:
        print(f"\n✅ Links fixed! Run check-broken-links.py to verify.")
    else:
        print(f"\n✅ No fixable links found (already fixed or manual intervention needed).")
    
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
