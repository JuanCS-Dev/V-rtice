"""Parse coverage audit JSON to generate markdown table.

Phase 1.5 of MAXIMUS Full System Audit.

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import json

# Load coverage data
with open('coverage_full_audit.json') as f:
    data = json.load(f)

results = []
for filepath, metrics in data['files'].items():
    # Skip venv, __pycache__, audit_results, htmlcov
    if any(skip in filepath for skip in ['venv', '__pycache__', 'audit_results', 'htmlcov', '.pytest_cache']):
        continue

    summary = metrics['summary']
    results.append({
        'file': filepath,
        'statements': summary['num_statements'],
        'missing': summary['missing_lines'],
        'coverage': summary['percent_covered'],
        'branches': summary.get('num_branches', 0),
        'branch_coverage': summary.get('covered_branches', 0) / max(1, summary.get('num_branches', 1)) * 100 if summary.get('num_branches', 0) > 0 else 0
    })

# Sort by coverage (lowest first)
results.sort(key=lambda x: x['coverage'])

# Output table
print("| File | Statements | Missing | Coverage | Branches | Branch Cov | Risk |")
print("|------|------------|---------|----------|----------|------------|------|")

for r in results[:100]:  # Top 100 lowest coverage
    risk = "🔴" if r['coverage'] < 30 else "🟡" if r['coverage'] < 70 else "🟢"
    file_short = r['file'][-60:] if len(r['file']) > 60 else r['file']
    print(f"| {file_short} | {r['statements']} | {r['missing']} | {r['coverage']:.1f}% | {r['branches']} | {r['branch_coverage']:.1f}% | {risk} |")

# Summary stats
total_stmts = sum(r['statements'] for r in results)
total_missing = sum(r['missing'] for r in results)
avg_coverage = (total_stmts - total_missing) / total_stmts * 100 if total_stmts > 0 else 0

print("\n**Summary:**")
print(f"- Total statements: {total_stmts}")
print(f"- Missing statements: {total_missing}")
print(f"- Average coverage: {avg_coverage:.2f}%")
print(f"- Files analyzed: {len(results)}")
print("\n**Risk Distribution:**")
print(f"- 🔴 Critical (<30%): {sum(1 for r in results if r['coverage'] < 30)}")
print(f"- 🟡 High (30-70%): {sum(1 for r in results if 30 <= r['coverage'] < 70)}")
print(f"- 🟢 Acceptable (70%+): {sum(1 for r in results if r['coverage'] >= 70)}")
