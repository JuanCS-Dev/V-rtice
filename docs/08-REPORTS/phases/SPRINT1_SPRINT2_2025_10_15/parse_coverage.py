import json
import sys

with open('coverage.json') as f:
    data = json.load(f)

# Filter consciousness modules (exclude tests, __pycache__)
modules = []
for filepath, filedata in data['files'].items():
    if 'consciousness/' in filepath and '__pycache__' not in filepath and 'test_' not in filepath:
        summary = filedata['summary']
        modules.append({
            'file': filepath,
            'statements': summary['num_statements'],
            'coverage': summary['percent_covered']
        })

# Sort by statements (descending)
modules.sort(key=lambda x: x['statements'], reverse=True)

# Print table
print(f"{'STATEMENTS':<12} {'COVERAGE':<10} {'FILE'}")
print("=" * 100)
for m in modules:
    coverage_str = f"{m['coverage']:.2f}%"
    # Mark <100% with indicator
    indicator = "❌" if m['coverage'] < 100 else "✅"
    print(f"{m['statements']:<12} {coverage_str:<10} {indicator} {m['file']}")

# Summary
total_modules = len(modules)
complete_modules = sum(1 for m in modules if m['coverage'] == 100)
incomplete_modules = total_modules - complete_modules

print("\n" + "=" * 100)
print(f"TOTAL: {total_modules} modules | ✅ {complete_modules} complete (100%) | ❌ {incomplete_modules} incomplete (<100%)")

# List incomplete modules
if incomplete_modules > 0:
    print("\n🎯 TARGET MODULES (<100%):")
    for m in modules:
        if m['coverage'] < 100:
            print(f"  - {m['file']}: {m['statements']} statements, {m['coverage']:.2f}%")
