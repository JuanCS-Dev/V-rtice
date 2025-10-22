#!/usr/bin/env python3
"""Fix PyTorch imports in performance modules to handle optional torch dependency."""

import re
from pathlib import Path

FILES_TO_FIX = [
    "performance/inference_engine.py",
    "performance/onnx_exporter.py",
    "performance/profiler.py",
    "performance/pruner.py",
    "performance/quantizer.py",
]

def fix_file(file_path: Path):
    """Add TYPE_CHECKING imports to a file."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already fixed
    if "from __future__ import annotations" in content:
        print(f"✓ {file_path} already fixed")
        return

    # Find the docstring end
    docstring_pattern = r'""".*?"""'
    match = re.search(docstring_pattern, content, re.DOTALL)

    if not match:
        print(f"✗ Could not find docstring in {file_path}")
        return

    docstring_end = match.end()

    # Insert after docstring
    new_content = (
        content[:docstring_end] +
        "\n\nfrom __future__ import annotations\n" +
        content[docstring_end:]
    )

    # Add TYPE_CHECKING import if torch is imported
    if "import torch" in new_content:
        # Find the typing import line
        typing_pattern = r'from typing import ([^\n]+)'
        typing_match = re.search(typing_pattern, new_content)

        if typing_match:
            # Add TYPE_CHECKING to existing typing import
            imports = typing_match.group(1)
            if "TYPE_CHECKING" not in imports:
                new_imports = f"TYPE_CHECKING, {imports}"
                new_content = new_content.replace(
                    f"from typing import {imports}",
                    f"from typing import {new_imports}"
                )

        # Add TYPE_CHECKING block after ImportError
        importerror_pattern = r'except ImportError:\s+TORCH_AVAILABLE = False'
        if re.search(importerror_pattern, new_content):
            new_content = re.sub(
                importerror_pattern,
                r'''except ImportError:
    TORCH_AVAILABLE = False
    if TYPE_CHECKING:
        import torch
        import torch.nn as nn''',
                new_content
            )

    # Write back
    with open(file_path, 'w') as f:
        f.write(new_content)

    print(f"✓ Fixed {file_path}")

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent

    for file_rel in FILES_TO_FIX:
        file_path = base_dir / file_rel
        if file_path.exists():
            fix_file(file_path)
        else:
            print(f"✗ File not found: {file_path}")
