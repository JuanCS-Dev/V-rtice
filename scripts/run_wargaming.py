#!/usr/bin/env python3
"""
Wargaming CLI - Run wargaming validation from command line.

Usage:
    python scripts/run_wargaming.py --apv-id APV_001 --patch-id PATCH_001
    python scripts/run_wargaming.py --cve-id CVE-2024-1234

Author: MAXIMUS Team
Date: 2025-10-11
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend/services"))

from wargaming_crisol.exploit_database import load_exploit_database, get_exploit_for_apv
from wargaming_crisol.two_phase_simulator import validate_patch_via_wargaming


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run wargaming validation")
    parser.add_argument("--apv-id", required=True, help="APV ID")
    parser.add_argument("--patch-id", required=True, help="Patch ID")
    parser.add_argument("--cve-id", help="CVE ID (optional)")
    parser.add_argument("--target-url", default="http://localhost:8080", help="Target URL")
    parser.add_argument("--output", help="Output JSON file")
    
    args = parser.parse_args()
    
    print("🎯 MAXIMUS Wargaming Validation")
    print("=" * 50)
    print()
    
    # Load exploit database
    print("Loading exploit database...")
    db = load_exploit_database()
    stats = db.get_statistics()
    print(f"✓ Loaded {stats['total']} exploits")
    print(f"  CWE Coverage: {len(stats['cwe_coverage'])}")
    print()
    
    # Mock APV and Patch (in production: load from database)
    from unittest.mock import Mock
    
    apv = Mock()
    apv.apv_id = args.apv_id
    apv.cve_id = args.cve_id or f"CVE-{args.apv_id}"
    apv.cwe_ids = ["CWE-89"]  # Example
    
    patch = Mock()
    patch.patch_id = args.patch_id
    patch.unified_diff = "..."
    
    # Find exploit
    print(f"Finding exploit for {apv.cve_id}...")
    exploit = get_exploit_for_apv(apv, db)
    
    if not exploit:
        print(f"❌ No exploit found for {apv.cve_id}")
        sys.exit(1)
    
    print(f"✓ Using exploit: {exploit.name}")
    print()
    
    # Run wargaming
    print("Running two-phase wargaming...")
    print()
    
    result = await validate_patch_via_wargaming(
        apv=apv,
        patch=patch,
        exploit=exploit,
        target_url=args.target_url
    )
    
    # Print results
    print()
    print("=" * 50)
    print(result.summary())
    print("=" * 50)
    print()
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"✓ Results saved to {args.output}")
    
    # Exit code
    sys.exit(0 if result.patch_validated else 1)


if __name__ == "__main__":
    asyncio.run(main())
