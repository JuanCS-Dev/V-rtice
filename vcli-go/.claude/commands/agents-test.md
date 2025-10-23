Execute TESTER agent for comprehensive testing and coverage analysis.

**What it does:**
- Runs all tests in target path
- Measures code coverage
- Validates quality gates (configurable thresholds)
- Generates coverage reports
- Identifies untested code paths
- Runs integration and unit tests

**Usage examples:**
- "Use agents-test to validate ./internal/auth with 80% coverage minimum"
- "Run TESTER on entire codebase with coverage report"
- "agents-test: check test coverage for ./cmd/api"

**Key flags:**
- `--targets <path>` - Target paths for testing (default: ./...)
- `--coverage` - Generate coverage report
- `--min <percentage>` - Minimum coverage threshold (fails if below)
- `--integration` - Run integration tests only
- `--unit` - Run unit tests only

**Quality gates:**
- Coverage threshold (e.g., --min 80)
- Test failure count (zero tolerance)
- Performance benchmarks (optional)

**Output:**
- Test results summary
- Coverage percentage per package
- Detailed coverage report (HTML if requested)
- List of untested functions/lines

Provide target paths and desired coverage threshold. The agent will execute all tests and report results.
