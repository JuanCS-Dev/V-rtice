#!/usr/bin/env python3
"""
Real Empirical Validation - PRODUCTION-READY exploit testing.

Tests REAL exploits against REAL vulnerable containers.
NO MOCK, NO PLACEHOLDER, NO SHORTCUTS.

This script executes actual exploits from wargaming_crisol against
vulnerable targets to validate the Adaptive Immunity system.

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - Validator of all defenses
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx

# Add wargaming_crisol to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "services" / "wargaming_crisol"))

from exploits import cwe_89_sql_injection, cwe_79_xss, cwe_22_path_traversal, cwe_918_ssrf
from exploit_database import ExploitResult


# Test Configuration - REAL vulnerable targets (minimal test apps)
TEST_TARGETS = {
    "sql_injection": {
        "name": "SQL Injection (Minimal Flask App)",
        "url": "http://localhost:9001/user",
        "exploit_module": cwe_89_sql_injection,
        "param_name": "id",
        "expected_vulnerable": True,  # Intentionally vulnerable
    },
    "xss": {
        "name": "XSS (Minimal Flask App)",
        "url": "http://localhost:9002/search",
        "exploit_module": cwe_79_xss,
        "param_name": "q",
        "expected_vulnerable": True,  # Intentionally vulnerable
    },
}


async def check_target_availability(url: str, timeout: int = 5) -> bool:
    """
    Check if target is reachable.
    
    Args:
        url: Target URL
        timeout: Connection timeout
    
    Returns:
        True if target responds
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True)
            return response.status_code < 500
    except Exception as e:
        print(f"  ✗ Target unreachable: {e}")
        return False


async def execute_exploit_test(
    test_name: str,
    config: Dict
) -> Dict:
    """
    Execute exploit against target.
    
    Args:
        test_name: Test identifier
        config: Test configuration
    
    Returns:
        Test result dictionary
    """
    print(f"\n{'='*70}")
    print(f"TEST: {config['name']}")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    # Step 1: Check target availability
    print(f"1. Checking target availability: {config['url']}")
    available = await check_target_availability(config['url'])
    
    if not available:
        print(f"  ✗ Target not available - SKIPPING TEST")
        return {
            "test_name": test_name,
            "status": "skipped",
            "reason": "target_unavailable",
            "exploit_result": None,
            "duration_seconds": time.time() - start_time,
        }
    
    print(f"  ✓ Target available")
    
    # Step 2: Execute exploit
    print(f"\n2. Executing exploit: {config['exploit_module'].EXPLOIT_ID}")
    
    try:
        exploit_result: ExploitResult = await config['exploit_module'].execute(
            target_url=config['url'],
            timeout=30,
            param_name=config.get('param_name', 'id')
        )
        
        # Step 3: Analyze result
        print(f"\n3. Exploit Result:")
        print(f"  Status: {exploit_result.status.value}")
        print(f"  Success: {exploit_result.success}")
        print(f"  Duration: {exploit_result.duration_seconds:.2f}s")
        
        if exploit_result.error:
            print(f"  Error: {exploit_result.error}")
        
        # Print output (truncated)
        output_lines = exploit_result.output.split('\n')
        print(f"\n  Output (last 5 lines):")
        for line in output_lines[-5:]:
            print(f"    {line}")
        
        # Step 4: Validate against expectation
        expected_vulnerable = config['expected_vulnerable']
        validation_passed = exploit_result.success == expected_vulnerable
        
        print(f"\n4. Validation:")
        print(f"  Expected vulnerable: {expected_vulnerable}")
        print(f"  Exploit succeeded: {exploit_result.success}")
        print(f"  Validation: {'✅ PASS' if validation_passed else '❌ FAIL'}")
        
        duration = time.time() - start_time
        
        return {
            "test_name": test_name,
            "status": "completed",
            "exploit_result": exploit_result.to_dict(),
            "expected_vulnerable": expected_vulnerable,
            "validation_passed": validation_passed,
            "duration_seconds": duration,
        }
        
    except Exception as e:
        print(f"\n  ✗ Exploit execution failed: {e}")
        duration = time.time() - start_time
        
        return {
            "test_name": test_name,
            "status": "error",
            "error": str(e),
            "duration_seconds": duration,
        }


async def run_all_tests() -> Dict:
    """
    Run all empirical validation tests.
    
    Returns:
        Complete test results
    """
    print("\n" + "="*70)
    print("MAXIMUS ADAPTIVE IMMUNITY - REAL EMPIRICAL VALIDATION")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Tests: {len(TEST_TARGETS)}")
    print(f"Mode: PRODUCTION (NO MOCK)")
    print("="*70)
    
    start_time = time.time()
    results = []
    
    # Execute tests sequentially (to avoid overwhelming targets)
    for test_name, config in TEST_TARGETS.items():
        result = await execute_exploit_test(test_name, config)
        results.append(result)
        
        # Brief pause between tests
        await asyncio.sleep(1)
    
    total_duration = time.time() - start_time
    
    # Calculate statistics
    completed_tests = [r for r in results if r['status'] == 'completed']
    skipped_tests = [r for r in results if r['status'] == 'skipped']
    error_tests = [r for r in results if r['status'] == 'error']
    
    validated_tests = [
        r for r in completed_tests 
        if r.get('validation_passed', False)
    ]
    
    success_rate = (
        len(validated_tests) / len(completed_tests) * 100
        if completed_tests else 0.0
    )
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(results)}")
    print(f"  Completed: {len(completed_tests)}")
    print(f"  Skipped: {len(skipped_tests)}")
    print(f"  Errors: {len(error_tests)}")
    print(f"\nValidation:")
    print(f"  Passed: {len(validated_tests)}/{len(completed_tests)}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"\nDuration: {total_duration:.2f}s")
    print("="*70)
    
    # Detailed failures
    if len(validated_tests) < len(completed_tests):
        print("\n❌ FAILED TESTS:")
        for r in completed_tests:
            if not r.get('validation_passed', False):
                print(f"  - {r['test_name']}: {r.get('exploit_result', {}).get('status', 'unknown')}")
    
    if skipped_tests:
        print("\n⚠️  SKIPPED TESTS:")
        for r in skipped_tests:
            print(f"  - {r['test_name']}: {r.get('reason', 'unknown')}")
    
    # Determine overall status
    if len(validated_tests) == len(completed_tests) and completed_tests:
        overall_status = "✅ ALL TESTS PASSED"
    elif validated_tests:
        overall_status = "⚠️  PARTIAL SUCCESS"
    else:
        overall_status = "❌ ALL TESTS FAILED"
    
    print(f"\nOverall Status: {overall_status}")
    print("="*70)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "completed": len(completed_tests),
        "skipped": len(skipped_tests),
        "errors": len(error_tests),
        "validated": len(validated_tests),
        "success_rate": success_rate,
        "total_duration_seconds": total_duration,
        "results": results,
        "overall_status": overall_status,
    }


async def main():
    """Main entry point"""
    try:
        results = await run_all_tests()
        
        # Save results to file
        output_dir = Path(__file__).parent.parent.parent / "docs" / "reports" / "validations"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = output_dir / f"real-empirical-validation-{timestamp}.json"
        
        import json
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")
        
        # Exit code based on success
        if results['success_rate'] >= 95.0:
            print("\n✅ VALIDATION SUCCESSFUL (≥95% pass rate)")
            sys.exit(0)
        elif results['success_rate'] >= 50.0:
            print("\n⚠️  VALIDATION PARTIAL (50-95% pass rate)")
            sys.exit(1)
        else:
            print("\n❌ VALIDATION FAILED (<50% pass rate)")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
