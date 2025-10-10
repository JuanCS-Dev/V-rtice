#!/usr/bin/env python3
"""
Purpose: Check for broken internal links in markdown documentation
Usage: ./check-broken-links.py [--fix]
Author: MAXIMUS Team
Date: 2025-10-10
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict

def find_markdown_files(root: Path) -> List[Path]:
    """Find all markdown files in docs/ and root."""
    files = []
    files.extend(root.glob("docs/**/*.md"))
    files.extend(root.glob("*.md"))
    return sorted(files)

def extract_links(content: str, file_path: Path) -> List[Tuple[str, int]]:
    """Extract markdown links [text](path) with line numbers."""
    links = []
    # Match [text](path) - ignore external URLs
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    for line_num, line in enumerate(content.split('\n'), 1):
        for match in re.finditer(pattern, line):
            link_text = match.group(1)
            link_path = match.group(2)
            
            # Skip external URLs
            if link_path.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
                
            links.append((link_path, line_num))
    
    return links

def resolve_link(source_file: Path, link_path: str, root: Path) -> Path:
    """Resolve relative link to absolute path."""
    # Remove anchor if present
    clean_path = link_path.split('#')[0]
    
    if not clean_path:  # Pure anchor link
        return source_file
    
    # Resolve relative to source file's directory
    source_dir = source_file.parent
    resolved = (source_dir / clean_path).resolve()
    
    return resolved

def check_links(root: Path) -> Dict[str, List[Tuple[str, int, str]]]:
    """Check all links and return broken ones by file."""
    broken_by_file = defaultdict(list)
    total_links = 0
    broken_count = 0
    
    md_files = find_markdown_files(root)
    print(f"🔍 Scanning {len(md_files)} markdown files...\n")
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            links = extract_links(content, md_file)
            total_links += len(links)
            
            for link_path, line_num in links:
                target = resolve_link(md_file, link_path, root)
                
                if not target.exists():
                    broken_count += 1
                    relative_source = md_file.relative_to(root)
                    broken_by_file[str(relative_source)].append(
                        (link_path, line_num, str(target.relative_to(root) if target.is_relative_to(root) else target))
                    )
        except Exception as e:
            print(f"⚠️  Error processing {md_file}: {e}")
    
    return broken_by_file, total_links, broken_count

def suggest_fix(broken_path: str, root: Path) -> str:
    """Suggest possible correct path for broken link."""
    # Extract filename
    filename = Path(broken_path).name
    
    # Search for similar files
    matches = []
    for md_file in root.glob("**/*.md"):
        if md_file.name == filename:
            matches.append(md_file)
    
    if matches:
        return f" → Maybe: {matches[0].relative_to(root)}"
    return ""

def main():
    root = Path.cwd()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        📎 BROKEN LINKS CHECKER - MAXIMUS Vértice         ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    broken_by_file, total_links, broken_count = check_links(root)
    
    if not broken_by_file:
        print("✅ SUCCESS! No broken links found.\n")
        print(f"📊 Checked {total_links} internal links across all documentation.\n")
        return 0
    
    print(f"❌ BROKEN LINKS FOUND: {broken_count}/{total_links}\n")
    print("=" * 70)
    
    for source_file, broken_links in sorted(broken_by_file.items()):
        print(f"\n�� {source_file}")
        print("-" * 70)
        
        for link_path, line_num, resolved_path in broken_links:
            suggestion = suggest_fix(link_path, root)
            print(f"  Line {line_num}: [{link_path}]")
            print(f"    Target: {resolved_path} ❌")
            if suggestion:
                print(f"    {suggestion}")
    
    print("\n" + "=" * 70)
    print(f"\n📊 SUMMARY:")
    print(f"  • Total links checked: {total_links}")
    print(f"  • Broken links: {broken_count}")
    print(f"  • Files with issues: {len(broken_by_file)}")
    print(f"  • Success rate: {((total_links - broken_count) / total_links * 100):.1f}%")
    
    print("\n💡 TIP: Review and fix broken links manually.")
    print("   Most are likely due to recent reorganization.\n")
    
    return 1 if broken_count > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
