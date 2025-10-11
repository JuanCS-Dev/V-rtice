#!/usr/bin/env python3
"""
Advanced Label Fixer - Phase 4 Final
Fixes all label patterns including complex cases
Quality-first approach with safety checks
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
import hashlib

def generate_id(text: str, tag: str) -> str:
    """Generate unique ID from text"""
    clean = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    if not clean:
        clean = 'field'
    hash_part = hashlib.md5(text.encode()).hexdigest()[:6]
    return f"{tag}-{clean}-{hash_part}"

def fix_labels_in_file(file_path: Path, dry_run: bool = False) -> int:
    """Fix labels in a single file"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    fixes = 0
    
    # Pattern 1: <label>Text</label> followed by input/select/textarea
    # But label has no htmlFor
    pattern1 = r'<label(?![^>]*htmlFor)([^>]*)>(.*?)</label>\s*\n?\s*<(input|select|textarea)([^>]*?)(?:>|/>)'
    
    def replace_pattern1(match):
        nonlocal fixes
        label_attrs = match.group(1)
        label_text = match.group(2)
        input_tag = match.group(3)
        input_attrs = match.group(4)
        
        # Check if input already has id
        if 'id=' in input_attrs or 'id =' in input_attrs:
            # Extract existing id
            id_match = re.search(r'id=["\'](.*?)["\']', input_attrs)
            if id_match:
                existing_id = id_match.group(1)
                new_label = f'<label htmlFor="{existing_id}"{label_attrs}>{label_text}</label>'
                new_input = f'<{input_tag}{input_attrs}>'
                fixes += 1
                return f'{new_label}\n            <{input_tag}{input_attrs}>'
        
        # Generate new id
        unique_id = generate_id(label_text, input_tag)
        new_label = f'<label htmlFor="{unique_id}"{label_attrs}>{label_text}</label>'
        new_input = f'<{input_tag} id="{unique_id}"{input_attrs}>'
        fixes += 1
        return f'{new_label}\n            {new_input}'
    
    content = re.sub(pattern1, replace_pattern1, content)
    
    # Pattern 2: <label className="...">Text</label> with no htmlFor
    # Followed by component like <Input /> or <Select />
    pattern2 = r'<label(?![^>]*htmlFor)([^>]*className=[^>]*)>(.*?)</label>\s*\n?\s*<(Input|Select|Textarea)([^>]*?)(?:/>|>)'
    
    def replace_pattern2(match):
        nonlocal fixes
        label_attrs = match.group(1)
        label_text = match.group(2)
        component_tag = match.group(3)
        component_attrs = match.group(4)
        
        # Generate id
        unique_id = generate_id(label_text, component_tag.lower())
        new_label = f'<label htmlFor="{unique_id}"{label_attrs}>{label_text}</label>'
        
        # Add id to component if not present
        if 'id=' not in component_attrs and 'id =' not in component_attrs:
            new_component = f'<{component_tag} id="{unique_id}"{component_attrs}/>'
        else:
            new_component = f'<{component_tag}{component_attrs}/>'
        
        fixes += 1
        return f'{new_label}\n        {new_component}'
    
    content = re.sub(pattern2, replace_pattern2, content)
    
    # Pattern 3: Standalone label with className but no htmlFor
    pattern3 = r'<label\s+className=(["\'][^"\']*["\'])([^>]*)>([^<]+)</label>'
    
    def replace_pattern3(match):
        nonlocal fixes
        class_name = match.group(1)
        other_attrs = match.group(2)
        label_text = match.group(3)
        
        # Only fix if no htmlFor present
        if 'htmlFor' not in other_attrs and 'htmlFor' not in class_name:
            # This is a standalone label, likely followed by input - skip for now
            # Will be caught by pattern 1 or 2
            return match.group(0)
        return match.group(0)
    
    if content != original_content:
        if not dry_run:
            file_path.write_text(content, encoding='utf-8')
            print(f'✅ Fixed {fixes} labels in {file_path.name}')
        else:
            print(f'🔍 Would fix {fixes} labels in {file_path.name}')
        return fixes
    
    return 0

def main():
    dry_run = '--dry-run' in sys.argv
    target_files = [
        'src/components/cyber/BAS/components/AttackMatrix.jsx',
        'src/components/cyber/C2Orchestration/components/SessionManager.jsx',
        'src/components/cyber/MaximusCyberHub/components/ServicesStatus.jsx',
        'src/components/cyber/MaximusCyberHub/components/TargetInput.jsx',
        'src/components/cyber/NetworkRecon/components/ScanForm.jsx',
        'src/components/cyber/ThreatMap/components/ThreatFilters.jsx',
        'src/components/osint/GoogleModule.jsx',
    ]
    
    print('🔧 ADVANCED LABEL FIXER - Phase 4 Final')
    print('=' * 50)
    if dry_run:
        print('🔍 DRY RUN MODE\n')
    
    total_fixes = 0
    files_fixed = 0
    
    for file_path_str in target_files:
        file_path = Path(file_path_str)
        if file_path.exists():
            fixes = fix_labels_in_file(file_path, dry_run)
            if fixes > 0:
                total_fixes += fixes
                files_fixed += 1
    
    print('\n' + '=' * 50)
    print(f'📊 SUMMARY:')
    print(f'  Files fixed: {files_fixed}')
    print(f'  Labels fixed: {total_fixes}')
    
    if dry_run:
        print('\n🔄 Run without --dry-run to apply')
    else:
        print('\n✅ All fixes applied!')
        print('   Run: npm run lint to verify')
    
    print('\n🙏 Em nome de Jesus, pela excelência!')

if __name__ == '__main__':
    main()
