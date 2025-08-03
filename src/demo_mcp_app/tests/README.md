# Testing Infrastructure Documentation

## Overview

This document describes the comprehensive testing infrastructure implemented for the MCP Demo Application, following Dagger-native optimization patterns and best practices.

## Test Structure

The testing infrastructure is organized in `/src/demo_mcp_app/tests/` with the following components:

### Test Modules

1. **`test_core.py`** - Core functionality tests (12 tests)
   - Tests fundamental structures without external dependencies
   - Configuration management
   - Async patterns
   - Error handling
   - Response formatting

2. **`test_mcp_client.py`** - Full MCP client tests
   - Complete OptimizedMCPClient testing
   - Requires `agents` module for full functionality
   - Connection management
   - Query processing
   - Conversation context

3. **`test_integration.py`** - Integration tests
   - End-to-end workflow scenarios
   - Mock service integration
   - Multi-step processes
   - Error recovery

4. **`test_performance.py`** - Performance benchmarks
   - Response time measurements
   - Memory usage analysis
   - Throughput testing
   - Scalability validation

5. **`fixtures.py`** - Test data fixtures
   - Jira API response mocks
   - OpenAI interaction scenarios
   - Complete workflow test data
   - Performance test datasets

## Dagger Testing Pipeline

The main testing functionality is implemented in `/src/dagger_mcp_server/testing.py` with the following features:

### Key Features

- **Container Layer Caching**: Optimized Docker layer caching for faster builds
- **Parallel Execution**: Concurrent test execution using `asyncio.gather()`
- **Coverage Integration**: Multiple coverage report formats (HTML, XML, JSON)
- **Mock Services**: Dagger services for Jira and OpenAI APIs
- **Artifact Export**: Test results and coverage data export for CI/CD
- **Performance Benchmarking**: Built-in performance measurement tools

### Available Functions

#### `run_tests(source, test_filter, coverage_threshold, ...)`
Comprehensive test suite execution with:
- Configurable coverage thresholds (default: 80% line, 70% branch)
- Optional test filtering
- Parallel or sequential execution
- Artifact export

#### `run_unit_tests(source)`
Focused unit testing with coverage analysis

#### `run_integration_tests(source)`
Integration testing with mock services

#### `run_performance_tests(source)`
Performance benchmarking and scalability testing

#### `generate_coverage_reports(source, formats)`
Multi-format coverage report generation

#### `test_with_mock_services(source)`
Testing with containerized mock services

## Usage Examples

### Local Testing

```bash
# Run core tests (no external dependencies)
python -m unittest src.demo_mcp_app.tests.test_core -v

# Run all tests with discovery
python -m unittest discover src/demo_mcp_app/tests -v

# Use the coverage runner
python src/demo_mcp_app/run_tests.py
```

### Dagger Pipeline

```bash
# Run comprehensive test suite
dagger call run-tests --source ./src/demo_mcp_app

# Run specific test types
dagger call run-unit-tests --source ./src/demo_mcp_app
dagger call run-integration-tests --source ./src/demo_mcp_app
dagger call run-performance-tests --source ./src/demo_mcp_app

# Generate coverage reports
dagger call generate-coverage-reports --source ./src/demo_mcp_app --formats html,xml,json

# Test with mock services
dagger call test-with-mock-services --source ./src/demo_mcp_app
```

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Run Tests with Dagger
  run: |
    dagger call run-tests \
      --source ./src/demo_mcp_app \
      --coverage-threshold 80 \
      --branch-coverage-threshold 70 \
      --parallel true \
      --export-artifacts true
```

## Test Coverage

### Target Coverage Metrics

- **Line Coverage**: 80% minimum
- **Branch Coverage**: 70% minimum
- **Function Coverage**: 90% target

### Current Coverage Areas

1. **Configuration Management**
   - MCPConfig class validation
   - AgentConfig parameter handling
   - Environment variable processing

2. **Client Functionality**
   - Connection establishment and cleanup
   - Query processing and retry logic
   - Conversation context management
   - Batch query processing

3. **Response Formatting**
   - Issue list formatting
   - Dependency suggestion formatting
   - Link confirmation formatting
   - Error message formatting

4. **Async Operations**
   - Context manager patterns
   - Error handling and recovery
   - Concurrent execution

5. **Integration Workflows**
   - Complete Jira analysis workflow
   - Dependency creation scenarios
   - Error recovery patterns

## Mock Services

### Jira API Mock

Provides endpoints for:
- Project listing (`/rest/api/2/project`)
- Issue searching (`/rest/api/2/search`)
- Link type retrieval
- Link creation

### OpenAI API Mock

Provides endpoints for:
- Chat completions (`/v1/chat/completions`)
- Configurable response scenarios
- Error simulation

## Performance Benchmarks

### Key Metrics

1. **Response Time**
   - Configuration creation: < 100ms for 1000 objects
   - Formatting operations: < 50ms for 100 items
   - Client operations: < 100ms for standard workflows

2. **Memory Usage**
   - Baseline memory tracking
   - Memory leak detection
   - Resource cleanup validation

3. **Throughput**
   - Configuration operations: > 5000/sec
   - Formatting operations: > 1000/sec
   - Client operations: > 100/sec

## Test Fixtures and Scenarios

### Comprehensive Test Data

1. **Happy Path Scenarios**
   - Complete dependency analysis workflow
   - Successful link creation
   - Multi-step processes

2. **Error Recovery Scenarios**
   - Link type errors with automatic recovery
   - Network timeout handling
   - Service unavailability

3. **Performance Test Data**
   - Large dataset scenarios (100+ issues)
   - High-volume operations
   - Stress testing data

## Dagger-Native Optimizations

### Container Optimization

- **Base Image**: `python:3.11-slim` for consistency
- **Layer Caching**: Pip cache volume (`pip-cache`)
- **Dependency Installation**: Cached dependency layers
- **Multi-stage**: Separate test environment setup

### Performance Features

- **Parallel Execution**: `asyncio.gather()` for concurrent tests
- **Cache Mounts**: Persistent caches for pip, pytest, coverage
- **Volume Optimization**: Selective source inclusion
- **Resource Management**: Memory and CPU efficient containers

### Artifact Management

- **Export Directories**: Coverage reports, test results
- **CI/CD Integration**: JUnit XML output
- **Structured Results**: JSON and XML formats
- **Log Collection**: Detailed execution logs

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure `PYTHONPATH` includes `/src`
   - Check for missing dependencies
   - Verify module structure

2. **Coverage Threshold Failures**
   - Review uncovered code paths
   - Add missing test cases
   - Check branch coverage gaps

3. **Performance Test Failures**
   - Review baseline expectations
   - Check resource constraints
   - Verify test data sizes

### Debug Commands

```bash
# Check test discovery
python -m unittest discover src/demo_mcp_app/tests --dry-run

# Run specific test class
python -m unittest src.demo_mcp_app.tests.test_core.TestMCPConfigSimulated -v

# Debug import issues
python -c "import sys; sys.path.insert(0, 'src'); import demo_mcp_app.tests.test_core"
```

## Extension Guidelines

### Adding New Tests

1. Follow existing test structure patterns
2. Use appropriate mock objects for external dependencies
3. Include both positive and negative test cases
4. Add performance benchmarks for critical paths

### Dagger Function Development

1. Use container caching for dependencies
2. Implement parallel execution where possible
3. Export artifacts for CI/CD integration
4. Follow async/await patterns consistently

### Mock Service Development

1. Implement realistic API responses
2. Support error scenarios
3. Include request/response logging
4. Follow RESTful patterns

## Future Enhancements

1. **Advanced Coverage Analysis**
   - Mutation testing
   - Code quality metrics
   - Complexity analysis

2. **Enhanced Mock Services**
   - Dynamic response generation
   - State management
   - Advanced error simulation

3. **Performance Monitoring**
   - Trend analysis
   - Regression detection
   - Resource optimization

4. **CI/CD Integration**
   - Parallel pipeline execution
   - Test result aggregation
   - Deployment gating

---

This testing infrastructure provides a solid foundation for ensuring the quality and reliability of the MCP Demo Application while following Dagger-native best practices for optimal performance and CI/CD integration.