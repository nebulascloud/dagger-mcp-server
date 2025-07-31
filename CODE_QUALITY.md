# Code Quality Stage Documentation

This document describes the code quality stage implementation for the Dagger MCP Server CI pipeline.

## Overview

The code quality stage provides comprehensive automated code analysis including linting, formatting validation, and security scanning. All tools are containerized using Dagger for consistent execution across local and CI environments.

## Available Functions

### Main Function

#### `code_quality()`
Runs comprehensive code quality checks including:
- **Linting**: flake8, pylint, mypy, isort
- **Formatting**: black validation  
- **Security**: bandit, safety

Returns a detailed quality report with pass/fail status for each tool.

Usage:
```bash
dagger call code-quality
```

### Individual Tool Functions

#### `lint_with_flake8()`
Runs only flake8 linting for PEP 8 compliance checking.

Usage:
```bash
dagger call lint-with-flake8
```

#### `format_with_black()`
Validates code formatting with Black formatter.

Usage:
```bash
dagger call format-with-black
```

#### `security_scan()`
Runs security scanning with both Bandit and Safety tools.

Usage:
```bash
dagger call security-scan
```

## Tool Configuration

### Flake8
- Max line length: 88 characters
- Ignores: E203, W503 (Black compatibility)
- Configuration in `pyproject.toml`

### Black
- Line length: 88 characters
- Target version: Python 3.9+
- Configuration in `pyproject.toml`

### MyPy
- Strict type checking enabled
- Missing imports ignored for external dependencies
- Configuration in `pyproject.toml`

### isort
- Black-compatible profile
- Line length: 88 characters
- Configuration in `pyproject.toml`

### Pylint
- Max line length: 88 characters
- Disabled checks: missing-docstring, too-few-public-methods
- Configuration in `pyproject.toml`

### Bandit
- Recursive scanning of src/ directory
- Text format output
- Skips: B101 (assert statements)
- Configuration in `pyproject.toml`

### Safety
- Checks dependencies for known vulnerabilities
- Uses Safety database for vulnerability detection

## Quality Gates

The code quality stage implements configurable quality gates:

- **PASS**: All checks pass
- **PASS WITH WARNINGS**: All critical checks pass, but warnings exist (e.g., pylint warnings)
- **FAIL**: One or more critical checks fail

## Parallel Execution

Quality checks run in parallel using asyncio.gather() for optimal performance:
- All 7 tools execute simultaneously
- Results collected and aggregated
- Significant time savings over sequential execution

## Report Generation

The comprehensive quality report includes:
- Executive summary with pass/fail counts
- Overall status with color-coded indicators
- Detailed output from each tool (truncated for readability)
- Tool-specific exit codes

## Local Development

For local development, you can run individual tools:

```bash
# Linting
flake8 src/ --max-line-length=88 --extend-ignore=E203,W503
pylint src/ --max-line-length=88
mypy src/ --ignore-missing-imports
isort --check-only --diff src/

# Formatting
black --check --diff src/

# Security
bandit -r src/ -f txt --skip B101
safety check
```

## CI/CD Integration

The code quality stage is designed for CI/CD integration:
- Structured output formats for parsing
- Exit codes indicate success/failure
- Dagger Cloud tracing for execution monitoring
- Works with any CI platform (GitHub Actions, GitLab CI, Jenkins, etc.)

## Customization

Quality gates and tool configurations can be customized by:
1. Modifying `pyproject.toml` for tool-specific settings
2. Updating function parameters in the Dagger module
3. Adjusting parallel execution groupings
4. Customizing report format and content

## Dependencies

Required dependencies are automatically installed:
- black>=23.7.0
- flake8>=6.0.0
- mypy>=1.5.0
- isort>=5.12.0
- pylint>=3.0.0
- bandit>=1.7.0
- safety>=3.0.0

All dependencies are specified in `pyproject.toml` and `requirements.txt`.