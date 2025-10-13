"""
CPU profiling for HITL API.

Uses py-spy to generate CPU flamegraphs showing where time is spent.

Usage:
    # Profile running service
    python tests/performance/profile_cpu.py

    # Or use py-spy directly
    py-spy record --pid $(pgrep -f "uvicorn hitl.api.main") --output flamegraph.svg

Requirements:
    pip install py-spy

Output:
    - flamegraph.svg (interactive SVG)
    - profile.txt (text format)
"""

# Placeholder for performance profiling
# Execute py-spy manually or implement automated profiling here
print("Use py-spy to profile the running service:")
print("  py-spy record --pid $(pgrep -f 'uvicorn hitl.api.main') -o flamegraph.svg")
