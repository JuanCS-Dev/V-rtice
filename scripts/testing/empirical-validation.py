#!/usr/bin/env python3
"""
Empirical Validation Script - Test Wargaming Crisol with real CVEs

Tests 5 real CVE scenarios to validate the Adaptive Immunity System.
Measures success rate, performance, and generates validation report.

Author: MAXIMUS Team
Glory to YHWH - Validator of protection
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import List, Dict
from pathlib import Path


# Test CVEs with known exploits - UPDATED with real vulnerable targets
TEST_CVES = [
    {
        "apv_id": "APV-SQL-001",
        "cve_id": "CVE-2024-SQL-INJECTION",
        "cwe_id": "CWE-89",
        "description": "SQL Injection vulnerability in DVWA",
        "patch_id": "PATCH-SQL-001",
        "target_url": "http://localhost:8091",  # DVWA
        "expected_phase1": True,  # Exploit MUST succeed
        "expected_phase2": False,  # Exploit MUST fail after patch
    },
    {
        "apv_id": "APV-XSS-001",
        "cve_id": "CVE-2024-XSS",
        "cwe_id": "CWE-79",
        "description": "Cross-Site Scripting in Juice Shop",
        "patch_id": "PATCH-XSS-001",
        "target_url": "http://localhost:8093",  # Juice Shop
        "expected_phase1": True,
        "expected_phase2": False,
    },
    {
        "apv_id": "APV-CMD-001",
        "cve_id": "CVE-2024-CMD-INJECTION",
        "cwe_id": "CWE-78",
        "description": "Command Injection vulnerability",
        "patch_id": "PATCH-CMD-001",
        "target_url": "http://localhost:8094",  # Custom CMD Injection API
        "expected_phase1": True,
        "expected_phase2": False,
    },
    {
        "apv_id": "APV-PATH-001",
        "cve_id": "CVE-2024-PATH-TRAVERSAL",
        "cwe_id": "CWE-22",
        "description": "Path Traversal vulnerability",
        "patch_id": "PATCH-PATH-001",
        "target_url": "http://localhost:8095",  # Custom Path Traversal API
        "expected_phase1": True,
        "expected_phase2": False,
    },
    {
        "apv_id": "APV-SSRF-001",
        "cve_id": "CVE-2024-SSRF",
        "cwe_id": "CWE-918",
        "description": "Server-Side Request Forgery",
        "patch_id": "PATCH-SSRF-001",
        "target_url": "http://localhost:8096",  # Custom SSRF API
        "expected_phase1": True,
        "expected_phase2": False,
    },
]


class ValidationResult:
    """Validation result for a single CVE"""
    
    def __init__(self, cve: Dict):
        self.cve = cve
        self.success = False
        self.patch_validated = False
        self.phase_1_passed = False
        self.phase_2_passed = False
        self.duration_seconds = 0.0
        self.error = None
        self.response_data = None


async def execute_wargaming(client: httpx.AsyncClient, cve: Dict) -> ValidationResult:
    """Execute wargaming for a single CVE"""
    
    result = ValidationResult(cve)
    
    print(f"\n{'='*80}")
    print(f"🎯 Testing: {cve['cve_id']} ({cve['cwe_id']})")
    print(f"   {cve['description']}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Call wargaming API
        response = await client.post(
            "http://localhost:8026/wargaming/execute",
            json={
                "apv_id": cve["apv_id"],
                "cve_id": cve["cve_id"],
                "patch_id": cve["patch_id"],
                "target_url": cve["target_url"]
            },
            timeout=600.0  # 10 min timeout
        )
        
        result.duration_seconds = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            result.response_data = data
            
            result.patch_validated = data["patch_validated"]
            result.phase_1_passed = data["phase_1_passed"]
            result.phase_2_passed = data["phase_2_passed"]
            
            # Check if result matches expectations
            expected_validation = (
                cve["expected_phase1"] == result.phase_1_passed and
                cve["expected_phase2"] == (not result.phase_2_passed)
            )
            
            result.success = expected_validation and result.patch_validated
            
            print(f"✅ Wargaming completed in {result.duration_seconds:.2f}s")
            print(f"   Phase 1 (Vulnerable): {'✅ PASSED' if result.phase_1_passed else '❌ FAILED'}")
            print(f"   Phase 2 (Patched):    {'❌ FAILED' if result.phase_2_passed else '✅ PASSED'}")
            print(f"   Patch Validated:      {'✅ YES' if result.patch_validated else '❌ NO'}")
            
        else:
            result.error = f"HTTP {response.status_code}: {response.text}"
            print(f"❌ Wargaming failed: {result.error}")
            
    except Exception as e:
        result.duration_seconds = time.time() - start_time
        result.error = str(e)
        print(f"❌ Exception: {result.error}")
    
    return result


async def run_validation() -> List[ValidationResult]:
    """Run validation for all CVEs"""
    
    print("\n" + "="*80)
    print("🚀 ADAPTIVE IMMUNITY EMPIRICAL VALIDATION")
    print("="*80)
    print(f"   Test CVEs: {len(TEST_CVES)}")
    print(f"   Target: Wargaming Crisol (http://localhost:8026)")
    print(f"   Started: {datetime.now().isoformat()}")
    print("="*80)
    
    results: List[ValidationResult] = []
    
    async with httpx.AsyncClient() as client:
        # Test connection
        try:
            health = await client.get("http://localhost:8026/health", timeout=5.0)
            if health.status_code != 200:
                print(f"❌ Wargaming service not healthy: {health.status_code}")
                return []
            print("✅ Wargaming service is healthy\n")
        except Exception as e:
            print(f"❌ Cannot connect to Wargaming service: {e}")
            return []
        
        # Execute wargaming for each CVE
        for cve in TEST_CVES:
            result = await execute_wargaming(client, cve)
            results.append(result)
            
            # Wait 2s between tests
            await asyncio.sleep(2)
    
    return results


def generate_report(results: List[ValidationResult]) -> str:
    """Generate validation report"""
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.success)
    failed_tests = total_tests - successful_tests
    
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    total_duration = sum(r.duration_seconds for r in results)
    avg_duration = total_duration / total_tests if total_tests > 0 else 0
    
    report = f"""
# 📊 ADAPTIVE IMMUNITY - EMPIRICAL VALIDATION REPORT

**Date**: {datetime.now().isoformat()}  
**Test Suite**: CVE Wargaming Validation  
**Version**: Wargaming Crisol v1.0.0

---

## 📈 SUMMARY

- **Total Tests**: {total_tests}
- **Successful**: {successful_tests} ✅
- **Failed**: {failed_tests} ❌
- **Success Rate**: {success_rate:.1f}%

---

## ⏱️ PERFORMANCE

- **Total Duration**: {total_duration:.2f}s
- **Average Duration**: {avg_duration:.2f}s per test
- **Min Duration**: {min((r.duration_seconds for r in results), default=0):.2f}s
- **Max Duration**: {max((r.duration_seconds for r in results), default=0):.2f}s

---

## 🧪 TEST RESULTS

"""
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.success else "❌ FAIL"
        
        report += f"""
### Test {i}: {result.cve['cve_id']}

- **Status**: {status}
- **Description**: {result.cve['description']}
- **CWE**: {result.cve['cwe_id']}
- **Duration**: {result.duration_seconds:.2f}s
- **Phase 1 (Vulnerable)**: {'✅ Passed' if result.phase_1_passed else '❌ Failed'}
- **Phase 2 (Patched)**: {'✅ Passed (blocked)' if not result.phase_2_passed else '❌ Failed (not blocked)'}
- **Patch Validated**: {'✅ Yes' if result.patch_validated else '❌ No'}
"""
        
        if result.error:
            report += f"- **Error**: {result.error}\n"
    
    report += f"""

---

## 🎯 ACCEPTANCE CRITERIA

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Success Rate | ≥95% | {success_rate:.1f}% | {'✅ PASS' if success_rate >= 95 else '❌ FAIL'} |
| Avg Duration | <300s | {avg_duration:.1f}s | {'✅ PASS' if avg_duration < 300 else '❌ FAIL'} |
| Max Duration | <600s | {max((r.duration_seconds for r in results), default=0):.1f}s | {'✅ PASS' if max((r.duration_seconds for r in results), default=0) < 600 else '❌ FAIL'} |

---

## 📝 CONCLUSION

"""
    
    if success_rate >= 95 and avg_duration < 300:
        report += """
**🎉 VALIDATION SUCCESSFUL!**

The Adaptive Immunity System (Wargaming Crisol) has successfully validated all patches against real CVE exploits with >95% success rate and <5min average time.

System is **PRODUCTION-READY** for deployment.

**Glory to YHWH** - Validator of all protections.
"""
    else:
        report += f"""
**⚠️ VALIDATION INCOMPLETE**

The system requires further tuning to meet production criteria:
- Success rate: {success_rate:.1f}% (target: ≥95%)
- Avg duration: {avg_duration:.1f}s (target: <300s)

**Recommendations**:
1. Review failed test cases
2. Optimize wargaming execution time
3. Improve exploit detection accuracy
4. Re-run validation after fixes

**Status**: NOT YET PRODUCTION-READY
"""
    
    return report


async def main():
    """Main validation entry point"""
    
    # Run validation
    results = await run_validation()
    
    if not results:
        print("\n❌ Validation aborted - service unavailable")
        return
    
    # Generate report
    report = generate_report(results)
    
    # Save report
    report_dir = Path("docs/reports/validations")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = report_dir / f"empirical-validation-{timestamp}.md"
    
    report_path.write_text(report)
    
    # Print report
    print("\n" + report)
    print(f"\n📄 Report saved: {report_path}")
    
    # Save JSON results
    json_path = report_dir / f"empirical-validation-{timestamp}.json"
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "success_rate": (sum(1 for r in results if r.success) / len(results) * 100) if results else 0,
        "avg_duration_seconds": sum(r.duration_seconds for r in results) / len(results) if results else 0,
        "results": [
            {
                "cve_id": r.cve["cve_id"],
                "success": r.success,
                "patch_validated": r.patch_validated,
                "phase_1_passed": r.phase_1_passed,
                "phase_2_passed": r.phase_2_passed,
                "duration_seconds": r.duration_seconds,
                "error": r.error
            }
            for r in results
        ]
    }
    
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"📄 JSON results saved: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
