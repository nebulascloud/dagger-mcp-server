# Next.js/Firebase Dagger Pipeline Specification

> **Status:** Planning  
> **Version:** 1.0.0  
> **Date:** 2025-11-28  
> **Target Project:** Next.js application with Firebase Auth/Firestore, deployed on Vercel

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Module Specifications](#module-specifications)
4. [Service Container Definitions](#service-container-definitions)
5. [Function Specifications](#function-specifications)
6. [Configuration](#configuration)
7. [GitHub Actions Integration](#github-actions-integration)
8. [Migration Checklist](#migration-checklist)
9. [Open Planning Items](#open-planning-items)

---

## Executive Summary

### Objectives

1. **Containerized CI/CD** — Hermetic, reproducible test and build environments
2. **Local/CI Parity** — Identical pipeline execution on developer machines and GitHub Actions
3. **Flaky Test Mitigation** — Proper service readiness checks and isolated environments
4. **Coverage Visibility** — Clear reporting with regression detection
5. **Security Scanning** — Automated vulnerability and secret detection

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pipeline Language | Python | Leverage existing patterns, separation of concerns |
| Deployment | Vercel GitHub Integration | Keep what works; Dagger handles validation only |
| Firebase Emulators | Dagger Service Containers | Portability, isolation, deterministic networking |
| Test Framework | Existing Jest/Playwright | Wrap existing scripts, don't replace |

### What Dagger Does vs. Doesn't Do

| Dagger Handles | Vercel/Firebase Handle |
|----------------|------------------------|
| Run all tests in containers | Build and deploy Next.js app |
| Spin up Firebase emulators | Production Firebase services |
| Generate coverage reports | Preview deployments |
| Security scanning | SSL, CDN, edge functions |
| Status checks for PRs | Domain routing |

---

## Architecture Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Push                              │
└─────────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│  GitHub Actions              │   │  Vercel                      │
│  (Dagger Pipeline)           │   │  (Build & Deploy)            │
│                              │   │                              │
│  ┌────────────────────────┐  │   │  • Preview deployment        │
│  │ Dagger Engine          │  │   │  • Production deploy         │
│  │                        │  │   │    (after checks pass)       │
│  │  ┌──────────────────┐  │  │   │                              │
│  │  │ Firebase         │  │  │   └──────────────────────────────┘
│  │  │ Emulators        │  │  │
│  │  │ (Auth+Firestore) │  │  │
│  │  └────────┬─────────┘  │  │
│  │           │            │  │
│  │  ┌────────┴────────┐   │  │
│  │  │                 │   │  │
│  │  ▼                 ▼   │  │
│  │ Unit Tests    E2E Tests│  │
│  │ (Jest)      (Playwright)│ │
│  │                        │  │
│  │  + Firestore Rules     │  │
│  │  + Security Scans      │  │
│  │  + Coverage Reports    │  │
│  │                        │  │
│  └────────────────────────┘  │
│                              │
│  ✅ Status Check ────────────┼──────► Vercel waits for this
└──────────────────────────────┘
```

### Container Topology (Single Pipeline Run)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Dagger Engine                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Service Containers                      │   │
│  │                                                          │   │
│  │  ┌─────────────────┐  ┌─────────────────┐               │   │
│  │  │ Firebase Auth   │  │ Firestore       │               │   │
│  │  │ Emulator        │  │ Emulator        │               │   │
│  │  │ :9099           │  │ :8080           │               │   │
│  │  └─────────────────┘  └─────────────────┘               │   │
│  │                                                          │   │
│  │  ┌─────────────────┐                                    │   │
│  │  │ Emulator UI     │                                    │   │
│  │  │ :4000           │                                    │   │
│  │  └─────────────────┘                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                    (internal network)                           │
│                              │                                  │
│  ┌───────────────────────────┴─────────────────────────────┐   │
│  │                  Execution Containers                    │   │
│  │                                                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │ Unit Tests  │ │ E2E Tests   │ │ Security    │        │   │
│  │  │ (node:20)   │ │ (playwright)│ │ Scans       │        │   │
│  │  │             │ │             │ │             │        │   │
│  │  │ npm test    │ │ npm run     │ │ npm audit   │        │   │
│  │  │             │ │ test:e2e    │ │ + more      │        │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │   │
│  │                                                          │   │
│  │  ┌─────────────┐ ┌─────────────┐                        │   │
│  │  │ Firestore   │ │ Type Check  │                        │   │
│  │  │ Rules Test  │ │ + Lint      │                        │   │
│  │  │             │ │             │                        │   │
│  │  │ node script │ │ tsc + eslint│                        │   │
│  │  └─────────────┘ └─────────────┘                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Cached Volumes                           │  │
│  │  • node_modules cache                                     │  │
│  │  • npm cache                                              │  │
│  │  • Playwright browsers cache                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Specifications

### Proposed Directory Structure

```
dagger/
├── docs/
│   └── nextjs-firebase-pipeline-spec.md   # This document
├── src/
│   └── nextjs_pipeline/                   # New pipeline module
│       ├── __init__.py                    # Main Dagger module entry
│       ├── testing.py                     # Test orchestration
│       ├── security.py                    # Security scanning
│       ├── services.py                    # Firebase emulator services
│       ├── coverage.py                    # Coverage reporting
│       ├── dagger.json                    # Dagger module config
│       └── pyproject.toml                 # Python dependencies
├── pyproject.toml
└── README.md
```

### Module Descriptions

| Module | Purpose |
|--------|---------|
| `__init__.py` | Main entry point; exposes Dagger functions |
| `testing.py` | Test runner orchestration (unit, E2E, rules) |
| `security.py` | Security scanning (npm audit, secrets, etc.) |
| `services.py` | Firebase emulator service container definitions |
| `coverage.py` | Coverage report generation and threshold enforcement |

---

## Service Container Definitions

### Firebase Auth Emulator

```python
# Conceptual specification - not implementation code

FirebaseAuthEmulator:
  image: "node:20-slim"  # or dedicated firebase image
  ports:
    - 9099 (Auth API)
  environment:
    - FIREBASE_PROJECT_ID: <from config>
  healthcheck:
    endpoint: "http://localhost:9099/"
    interval: 2s
    timeout: 30s
  command: |
    npm install -g firebase-tools
    firebase emulators:start --only auth --project $FIREBASE_PROJECT_ID
```

### Firebase Firestore Emulator

```python
# Conceptual specification

FirestoreEmulator:
  image: "node:20-slim"
  ports:
    - 8080 (Firestore API)
  environment:
    - FIREBASE_PROJECT_ID: <from config>
    - FIRESTORE_EMULATOR_HOST: "localhost:8080"
  healthcheck:
    endpoint: "http://localhost:8080/"
    interval: 2s
    timeout: 30s
  command: |
    npm install -g firebase-tools
    firebase emulators:start --only firestore --project $FIREBASE_PROJECT_ID
```

### Combined Emulator Service (Recommended)

```python
# Conceptual specification - single container running both

FirebaseEmulators:
  image: "node:20"  # Full image for Java dependency
  ports:
    - 9099 (Auth)
    - 8080 (Firestore)
    - 4000 (Emulator UI)
  environment:
    - FIREBASE_PROJECT_ID: <from config>
  volumes:
    - firebase.json (from source)
    - firestore.rules (from source)
    - firestore.indexes.json (from source)
  healthcheck:
    # Check both services are ready
    auth: "http://localhost:9099/"
    firestore: "http://localhost:8080/"
  command: |
    npm install -g firebase-tools
    firebase emulators:start --only auth,firestore --project $FIREBASE_PROJECT_ID
```

---

## Function Specifications

### Main Entry Point (`__init__.py`)

| Function | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `run_all_checks` | Run complete validation suite | `source: Directory` | `CheckResult` |
| `run_tests` | Run all tests (unit + E2E + rules) | `source: Directory, coverage_threshold: int = 80` | `TestResult` |
| `run_unit_tests` | Run Jest unit tests only | `source: Directory` | `TestResult` |
| `run_e2e_tests` | Run Playwright E2E tests | `source: Directory` | `TestResult` |
| `run_firestore_rules_tests` | Test Firestore security rules | `source: Directory` | `TestResult` |
| `run_security_scans` | Run all security checks | `source: Directory` | `SecurityReport` |
| `generate_coverage_report` | Generate coverage artifacts | `source: Directory` | `Directory` |
| `lint_and_typecheck` | Run ESLint and TypeScript checks | `source: Directory` | `LintResult` |

### Testing Module (`testing.py`)

| Function | Description | Wraps npm Script |
|----------|-------------|------------------|
| `_create_base_container` | Create Node.js container with source | N/A |
| `_setup_dependencies` | Install npm dependencies with caching | `npm ci` |
| `_wait_for_emulators` | Block until Firebase emulators healthy | N/A |
| `execute_jest` | Run Jest with coverage | `npm test` |
| `execute_playwright` | Run Playwright in dedicated container | `npm run test:e2e` |
| `execute_rules_test` | Run Firestore rules test script | `node scripts/test-firestore-rules.js` |

### Security Module (`security.py`)

| Function | Description | Tool |
|----------|-------------|------|
| `run_npm_audit` | Check for vulnerable dependencies | `npm audit --json` |
| `run_secret_scan` | Detect hardcoded secrets | TruffleHog or Gitleaks |
| `run_eslint_security` | Security-focused linting | ESLint security plugin |
| `check_dependencies` | License and deprecation checks | `npm outdated`, license-checker |
| `generate_security_report` | Aggregate all scan results | Custom |

### Services Module (`services.py`)

| Function | Description |
|----------|-------------|
| `create_firebase_emulators` | Create combined Auth+Firestore service |
| `wait_for_auth_emulator` | Health check for Auth service |
| `wait_for_firestore_emulator` | Health check for Firestore service |
| `get_emulator_env_vars` | Return env vars for connecting to emulators |

### Coverage Module (`coverage.py`)

| Function | Description |
|----------|-------------|
| `parse_coverage_json` | Extract metrics from coverage output |
| `check_threshold` | Fail if coverage below threshold |
| `compare_to_baseline` | Detect coverage regression |
| `generate_html_report` | Create HTML coverage report |
| `generate_lcov_report` | Create LCOV for external tools |

---

## Configuration

### Pipeline Configuration File

The pipeline will read configuration from a `dagger-pipeline.yaml` in the target project root:

```yaml
# dagger-pipeline.yaml (example structure)

project:
  name: "my-nextjs-app"
  type: "nextjs-firebase"

firebase:
  project_id: "${FIREBASE_PROJECT_ID}"  # From environment
  emulators:
    auth_port: 9099
    firestore_port: 8080
    ui_port: 4000

testing:
  unit:
    enabled: true
    script: "npm test"
    coverage_threshold: 80
  e2e:
    enabled: true
    script: "npm run test:e2e"
    retries: 2  # Retry flaky tests
  firestore_rules:
    enabled: true
    script: "node scripts/test-firestore-rules.js"

security:
  npm_audit:
    enabled: true
    fail_on: "high"  # low, moderate, high, critical
  secret_scan:
    enabled: true
  eslint_security:
    enabled: true

coverage:
  line_threshold: 80
  branch_threshold: 70
  fail_on_regression: true
  regression_tolerance: 2  # Allow 2% drop

node:
  version: "20"
  package_manager: "npm"  # or "pnpm", "yarn"
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREBASE_PROJECT_ID` | Yes | Firebase project identifier |
| `FIREBASE_TOKEN` | For deploy only | CI token for Firebase CLI |
| `COVERAGE_BASELINE` | No | Previous coverage for regression check |

---

## GitHub Actions Integration

### Workflow File Structure

```yaml
# .github/workflows/ci.yml (specification)

name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    name: "Validate (Dagger)"
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Dagger Pipeline
        uses: dagger/dagger-for-github@v6
        with:
          version: "latest"
          verb: call
          module: ./dagger/src/nextjs_pipeline
          args: run-all-checks --source .

      - name: Upload Coverage Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage/

      - name: Upload Security Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: security-report
          path: security-report/

  # Vercel handles deployment via its own GitHub integration
  # This job just ensures checks pass before Vercel deploys to production
```

### Required GitHub Settings

1. **Branch Protection Rules:**
   - Require status checks before merging
   - Required check: `validate`

2. **Vercel Integration:**
   - Configure to wait for GitHub checks before production deploy
   - Preview deploys can proceed immediately

---

## Migration Checklist

### Phase 1: Foundation (This Repository)

- [ ] Create `nextjs_pipeline` module structure
- [ ] Implement base container creation with Node.js
- [ ] Implement npm dependency caching
- [ ] Create Firebase emulator service definitions
- [ ] Implement health check utilities
- [ ] Write configuration file parser

### Phase 2: After Copying to Target Project

- [ ] **Map existing npm scripts** (see [Open Planning Items](#open-planning-items))
- [ ] Validate emulator service connectivity
- [ ] Test Jest execution in container
- [ ] Test Playwright execution in container
- [ ] Test Firestore rules script execution
- [ ] Tune retry/timeout values for flaky test mitigation

### Phase 3: Security & Coverage

- [ ] Implement npm audit scanning
- [ ] Implement secret scanning
- [ ] Implement coverage report generation
- [ ] Implement coverage threshold enforcement
- [ ] Implement coverage regression detection

### Phase 4: GitHub Actions Integration

- [ ] Create workflow file
- [ ] Configure branch protection
- [ ] Configure Vercel to wait for checks
- [ ] Test full PR workflow

### Phase 5: Polish

- [ ] Documentation
- [ ] Local developer experience (easy commands)
- [ ] Performance optimization (parallelization)
- [ ] Error message improvements

---

## Open Planning Items

> These items require information from the target Next.js project and should be addressed after copying this pipeline to that repository.

### 🔲 npm Script Mapping

**Action Required:** Audit `package.json` in target project to map existing scripts.

| Pipeline Function | Expected npm Script | Needs Verification |
|-------------------|--------------------|--------------------|
| Unit tests | `npm test` | ⏳ |
| E2E tests | `npm run test:e2e` | ⏳ |
| Lint | `npm run lint` | ⏳ |
| Type check | `npm run typecheck` or `npx tsc --noEmit` | ⏳ |
| Build | `npm run build` | ⏳ |
| Firestore rules test | `node scripts/test-firestore-rules.js` | ⏳ |

### 🔲 Firebase Configuration Files

**Action Required:** Confirm presence and location of:

- [ ] `firebase.json`
- [ ] `firestore.rules`
- [ ] `firestore.indexes.json`
- [ ] `.firebaserc` (if using aliases)

### 🔲 Environment Variables

**Action Required:** Document all environment variables needed for tests:

- [ ] Firebase config vars
- [ ] API endpoints for mocking
- [ ] Feature flags

### 🔲 Playwright Configuration

**Action Required:** Review Playwright setup for container compatibility:

- [ ] Browser requirements (Chromium only? All browsers?)
- [ ] Base URL configuration
- [ ] Timeout settings
- [ ] Screenshot/trace settings

### 🔲 Flaky Test Analysis

**Action Required:** Identify specific flaky tests and root causes:

| Test File | Test Name | Flakiness Cause | Mitigation |
|-----------|-----------|-----------------|------------|
| ⏳ | ⏳ | ⏳ | ⏳ |

### 🔲 Coverage Baseline

**Action Required:** Establish current coverage baseline:

- [ ] Line coverage: __%
- [ ] Branch coverage: __%
- [ ] Function coverage: __%

### 🔲 Project Structure Verification

**Action Required:** Confirm directory structure:

```
project-root/
├── frontend/          # Is this the Next.js app root?
│   ├── src/
│   ├── e2e/
│   ├── package.json
│   └── ...
├── firebase.json      # Or inside frontend/?
└── ...
```

### 🔲 Existing Docker Setup Review

**Action Required:** Document current Docker Compose configuration for reference:

- [ ] Which services are defined?
- [ ] Port mappings
- [ ] Volume mounts
- [ ] Environment variables

---

## Local Development Testing

### Overview

In addition to CI/CD, the pipeline supports local development workflows where you can run your application against both Firebase Emulators and the live Firebase Cloud service simultaneously on different ports.

### Why This Approach?

| Benefit | Description |
|---------|-------------|
| **Rapid Feedback** | Switch between tabs to compare emulator vs cloud behavior |
| **Catch Environment Bugs** | Some issues only manifest against real services (latency, quotas, edge cases) |
| **Safe Experimentation** | Test destructive operations against emulators, verify read operations against cloud |
| **No Context Switching** | No need to restart the app or change environment variables manually |

### Dual-Environment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Local Machine                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Dagger Engine                           │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │         Firebase Emulators                      │    │   │
│  │  │         (Auth :9099, Firestore :8080)           │    │   │
│  │  └──────────────────────┬──────────────────────────┘    │   │
│  │                         │                                │   │
│  │                         ▼                                │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  Next.js App (Emulator Mode)                    │    │   │
│  │  │  http://localhost:3001                          │    │   │
│  │  │                                                 │    │   │
│  │  │  NEXT_PUBLIC_USE_EMULATOR=true                  │    │   │
│  │  │  FIRESTORE_EMULATOR_HOST=emulator:8080          │    │   │
│  │  │  FIREBASE_AUTH_EMULATOR_HOST=emulator:9099      │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Next.js App (Cloud Mode)                                │  │
│  │  http://localhost:3002                                   │  │
│  │                                                          │  │
│  │  NEXT_PUBLIC_USE_EMULATOR=false                          │  │
│  │  (Uses real Firebase project credentials)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│                    ┌──────────────────┐                        │
│                    │  Firebase Cloud  │                        │
│                    │  (Production or  │                        │
│                    │   Dev Project)   │                        │
│                    └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘

Browser Tabs:
  • Tab 1: http://localhost:3001  →  Emulator environment
  • Tab 2: http://localhost:3002  →  Cloud environment
```

### Proposed Dagger Functions

| Function | Description | Ports |
|----------|-------------|-------|
| `dev_emulator` | Run app against Firebase Emulators | App: 3001, Emulators: 9099/8080 |
| `dev_cloud` | Run app against Firebase Cloud | App: 3002 |
| `dev_dual` | Run both simultaneously | 3001 (emulator) + 3002 (cloud) |
| `dev_emulators_only` | Start only the emulators (for manual app start) | 9099/8080/4000 |

### Usage Examples

```bash
# Start both environments simultaneously
dagger call dev-dual --source .

# Start only the emulator environment
dagger call dev-emulator --source .

# Start only the cloud environment (requires Firebase credentials)
dagger call dev-cloud --source . --firebase-config ./firebase-credentials.json

# Start just the emulators (run your own app outside Dagger)
dagger call dev-emulators-only --source .
```

### Function Specification: `dev_dual`

```python
# Conceptual specification

def dev_dual(source: Directory, firebase_config: Secret) -> Service:
    """
    Start the application in two modes simultaneously.
    
    Returns a composite service exposing:
      - http://localhost:3001 (emulator mode)
      - http://localhost:3002 (cloud mode)
      - http://localhost:4000 (emulator UI)
    
    Prerequisites:
      - Source must be buildable with `npm run build`
      - firebase_config must contain valid Firebase credentials
    """
    
    # 1. Start Firebase Emulators as a background service
    emulators = start_firebase_emulators(source)
    
    # 2. Build the Next.js application once
    build_output = build_nextjs(source)
    
    # 3. Start emulator-connected instance
    emulator_app = (
        container()
        .with_service_binding("emulator", emulators)
        .with_env("NEXT_PUBLIC_USE_EMULATOR", "true")
        .with_env("FIRESTORE_EMULATOR_HOST", "emulator:8080")
        .with_env("FIREBASE_AUTH_EMULATOR_HOST", "emulator:9099")
        .with_exposed_port(3001)
        .with_exec(["npm", "start", "--", "-p", "3001"])
    )
    
    # 4. Start cloud-connected instance
    cloud_app = (
        container()
        .with_secret("FIREBASE_CONFIG", firebase_config)
        .with_env("NEXT_PUBLIC_USE_EMULATOR", "false")
        .with_exposed_port(3002)
        .with_exec(["npm", "start", "--", "-p", "3002"])
    )
    
    # 5. Return composite service
    return compose_services(emulator_app, cloud_app, emulators)
```

### Hot Reload Development (Option A — Recommended)

For active development with instant hot reload, Dagger manages the infrastructure while you run Next.js locally.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Local Machine                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Terminal 1: Dagger Services                             │  │
│  │                                                          │  │
│  │  $ dagger call dev-services --source .                   │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Firebase Emulators (containerized)                │  │  │
│  │  │                                                    │  │  │
│  │  │  • Auth Emulator      → localhost:9099             │  │  │
│  │  │  • Firestore Emulator → localhost:8080             │  │  │
│  │  │  • Emulator UI        → localhost:4000             │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                         (localhost)                             │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Terminal 2: Next.js Dev Server (local, not containerized)│  │
│  │                                                          │  │
│  │  $ npm run dev:emulator                                  │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Next.js with Hot Reload                           │  │  │
│  │  │                                                    │  │  │
│  │  │  • App running         → localhost:3000            │  │  │
│  │  │  • Instant HMR on save                             │  │  │
│  │  │  • Full source maps                                │  │  │
│  │  │  • Connected to emulators above                    │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Browser: http://localhost:3000                                │
│  Emulator UI: http://localhost:4000                            │
└─────────────────────────────────────────────────────────────────┘
```

#### Dagger Function: `dev_services`

```python
# Conceptual specification

def dev_services(source: Directory) -> Service:
    """
    Start Firebase Emulators as background services for local development.
    
    Exposes:
      - localhost:9099 (Auth Emulator)
      - localhost:8080 (Firestore Emulator)
      - localhost:4000 (Emulator UI)
    
    The emulators run in containers but ports are forwarded to localhost,
    allowing your local Next.js dev server to connect.
    """
    
    return (
        dag.container()
        .from_("node:20")
        .with_exec(["npm", "install", "-g", "firebase-tools"])
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exposed_port(9099)   # Auth
        .with_exposed_port(8080)   # Firestore
        .with_exposed_port(4000)   # UI
        .with_exec([
            "firebase", "emulators:start",
            "--only", "auth,firestore",
            "--project", "demo-project"
        ])
        .as_service()
    )
```

#### Required npm Scripts in Target Project

Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "dev:emulator": "cross-env NEXT_PUBLIC_USE_EMULATOR=true FIRESTORE_EMULATOR_HOST=localhost:8080 FIREBASE_AUTH_EMULATOR_HOST=localhost:9099 next dev",
    "dev:cloud": "cross-env NEXT_PUBLIC_USE_EMULATOR=false next dev --port 3001"
  }
}
```

#### Workflow: Day-to-Day Development

**Step 1: Start Emulators (once per session)**
```bash
# Terminal 1 - Leave this running
cd your-project
dagger call dev-services --source .

# Output:
# ✓ Firebase Emulators started
# ✓ Auth Emulator:      http://localhost:9099
# ✓ Firestore Emulator: http://localhost:8080
# ✓ Emulator UI:        http://localhost:4000
```

**Step 2: Start Next.js Dev Server**
```bash
# Terminal 2 - Your development terminal
cd your-project/frontend
npm run dev:emulator

# Output:
# ✓ Ready on http://localhost:3000
# ✓ Connected to Firebase Emulators
```

**Step 3: Develop with Hot Reload**
- Edit any file → Browser updates instantly
- Changes to React components → Hot Module Replacement
- Changes to API routes → Auto-restart
- All requests go to containerized emulators

**Step 4: (Optional) Test Against Cloud**
```bash
# Terminal 3 - Cloud comparison
npm run dev:cloud

# Opens on port 3001, connected to real Firebase
```

#### Workflow: Quick Comparison Testing

When you want to quickly compare emulator vs cloud behavior:

```bash
# Terminal 1: Emulators (Dagger)
dagger call dev-services --source .

# Terminal 2: App on emulators
npm run dev:emulator          # → localhost:3000

# Terminal 3: App on cloud
npm run dev:cloud             # → localhost:3001

# Browser tabs:
#   Tab 1: http://localhost:3000 (emulator)
#   Tab 2: http://localhost:3001 (cloud)
```

#### Environment Variable Reference

| Variable | Emulator Mode | Cloud Mode |
|----------|---------------|------------|
| `NEXT_PUBLIC_USE_EMULATOR` | `true` | `false` |
| `FIRESTORE_EMULATOR_HOST` | `localhost:8080` | (not set) |
| `FIREBASE_AUTH_EMULATOR_HOST` | `localhost:9099` | (not set) |

#### Benefits of This Approach

| Benefit | Description |
|---------|-------------|
| **Instant Feedback** | Sub-second hot reload, no container rebuild |
| **Full Debugging** | Local Node.js means full debugger access, source maps |
| **Isolated Services** | Emulators run in containers, clean slate each start |
| **No Docker Compose** | Dagger replaces your docker-compose for emulators |
| **Same Emulator Config** | Uses your project's `firebase.json` and rules files |
| **Easy Cleanup** | Ctrl+C stops emulators, no orphaned containers |

#### Comparison: Option A vs Option B

| Aspect | Option A (Recommended) | Option B (Full Container) |
|--------|------------------------|---------------------------|
| Hot reload speed | Instant (~100ms) | Slower (~2-5s) |
| Debugging | Full IDE debugger | Remote debugging required |
| Node.js required locally | Yes | No |
| Matches CI exactly | Close (same emulators) | Exact match |
| Setup complexity | Simple | More complex |
| Use case | Daily development | CI parity verification |

**When to use Option B instead:**
- Verifying behavior matches CI exactly before pushing
- Testing on a machine without Node.js installed
- Debugging container-specific issues

### Configuration Addition

```yaml
# Addition to dagger-pipeline.yaml

local_dev:
  emulator_app_port: 3001
  cloud_app_port: 3002
  emulator_ui_port: 4000
  
  # For cloud mode, which Firebase project to use
  cloud_project: "my-app-dev"  # Use dev project, not production!
  
  # Hot reload mode
  watch_mode: false  # Set to true for Option B above
  
  # Build before running (set to false if using dev server)
  prebuild: true
```

### Safety Considerations

| Risk | Mitigation |
|------|------------|
| Accidentally using production Firebase | Use a dedicated dev Firebase project for cloud mode |
| Credentials in container | Use Dagger secrets, never bake into image |
| Port conflicts | Configurable ports, clear error if ports in use |
| Data pollution | Cloud mode should use dev project with test data only |

---

## Appendix A: Comparison with Current Python Pipeline

| Aspect | Current (Python MCP App) | New (Next.js/Firebase) |
|--------|-------------------------|------------------------|
| Base image | `python:3.12-slim` | `node:20-alpine` |
| Dependency install | `pip install` | `npm ci` |
| Cache volumes | pip cache | npm cache, node_modules |
| Test runner | pytest | Jest |
| E2E tests | N/A | Playwright |
| Coverage tool | coverage.py | c8/istanbul via Jest |
| Mock services | Flask-based mocks | Firebase Emulators |
| Security: dependencies | pip-audit | npm audit |
| Security: SAST | Bandit | ESLint security |
| Security: secrets | detect-secrets | TruffleHog/Gitleaks |
| Package build | wheel/sdist | N/A (Vercel builds) |
| Deployment | Container registry | Vercel (external) |

---

## Appendix B: Reused Patterns from Current Pipeline

The following patterns from the existing `dagger_mcp_server` will be adapted:

1. **Async Orchestration** (`testing.py`)
   - `asyncio.gather()` for parallel test execution
   - Structured result aggregation

2. **Container Caching Strategy** (`testing.py`)
   - Volume mounts for dependency caches
   - Cache key strategies

3. **Service Health Checks** (new, but pattern from `testing.py`)
   - Wait-for-healthy before test execution

4. **Report Generation** (`security.py`)
   - JSON report aggregation
   - Summary generation

5. **Multi-format Output** (`building.py`)
   - Coverage in multiple formats (HTML, JSON, LCOV)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-28 | - | Initial specification |
