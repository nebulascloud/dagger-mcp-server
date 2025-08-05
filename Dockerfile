# Multi-stage Dockerfile for Jira Dependency Analyzer MCP Application
# Optimized for development, testing, and production environments

# Base stage with common dependencies
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Development stage
FROM base AS development

# Install development dependencies 
RUN pip install --no-cache-dir -e .[dev]

# Install additional development tools
RUN pip install --no-cache-dir \
    ipython \
    jupyter \
    debugpy \
    pytest-xdist

# Create development user
RUN groupadd -r devuser && useradd -r -g devuser -d /app -s /bin/bash devuser
RUN chown -R devuser:devuser /app

USER devuser

# Development entry point
CMD ["python", "-m", "jira_dependency_analyzer.cli", "--debug"]

# Testing stage
FROM base AS testing

# Install testing and coverage dependencies
RUN pip install --no-cache-dir \
    pytest>=7.4.0 \
    pytest-asyncio>=0.21.0 \
    pytest-mock>=3.11.0 \
    pytest-cov>=4.1.0 \
    coverage>=7.0.0

# Copy test files
COPY tests/ ./tests/
COPY run_tests.py ./

# Create test user
RUN groupadd -r testuser && useradd -r -g testuser -d /app -s /bin/bash testuser
RUN chown -R testuser:testuser /app

USER testuser

# Testing entry point
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=jira_dependency_analyzer"]

# Production stage (optimized and hardened)
FROM python:3.11-slim AS production

# Security: Install only necessary system packages
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Security: Create non-root user
RUN groupadd -r mcpuser && \
    useradd -r -g mcpuser -d /app -s /sbin/nologin mcpuser

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install only production dependencies
RUN pip install --no-cache-dir --no-dev -e . && \
    pip cache purge

# Security: Set proper file permissions
RUN chown -R mcpuser:mcpuser /app && \
    chmod -R 755 /app

# Security: Switch to non-root user
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import jira_dependency_analyzer; print('OK')" || exit 1

# Expose port (if needed)
EXPOSE 8080

# Production entry point
ENTRYPOINT ["python", "-m", "jira_dependency_analyzer.cli"]
CMD ["--help"]

# Metadata
LABEL maintainer="Nebulas Cloud <dev@nebulas.com.au>" \
      version="0.1.0" \
      description="AI-powered Jira work analysis and dependency suggestion tool" \
      org.opencontainers.image.source="https://github.com/nebulascloud/dagger-mcp-server" \
      org.opencontainers.image.documentation="https://github.com/nebulascloud/dagger-mcp-server/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT"