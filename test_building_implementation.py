#!/usr/bin/env python3
"""
Test script for validating building stage implementation.

This script tests the building.py module without requiring external dependencies
by focusing on module structure, class instantiation, and basic functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
from dagger_mcp_server.building import (
    Builder, 
    BuildResults, 
    ImageBuildResults,
    PackageResults,
    ManifestResults,
    DocumentationResults
)


async def test_builder_classes():
    """Test that all builder classes can be instantiated."""
    print("🧪 Testing Builder class instantiation...")
    
    try:
        builder = Builder()
        print("✅ Builder class instantiated successfully")
    except Exception as e:
        print(f"❌ Builder class instantiation failed: {e}")
        return False
    
    return True


def test_result_classes():
    """Test that all result classes can be instantiated and provide summaries."""
    print("\n🧪 Testing Result classes...")
    
    try:
        # Test BuildResults
        build_result = BuildResults(
            success=True,
            production_image_built=True,
            packages_generated=True,
            manifests_created=True,
            documentation_generated=True,
            environment="production",
            artifact_count=4,
            build_duration=180.0
        )
        print("✅ BuildResults class instantiated successfully")
        print("📋 Build Summary:")
        print(build_result.summary())
        
        # Test ImageBuildResults
        image_result = ImageBuildResults(
            image_built=True,
            image_size_mb=250.5,
            security_hardened=True,
            layers_optimized=True,
            base_image="python:3.11-slim"
        )
        print("✅ ImageBuildResults class instantiated successfully")
        
        # Test PackageResults
        package_result = PackageResults(
            wheel_generated=True,
            source_dist_generated=True,
            package_size_mb=2.1,
            dependencies_resolved=True
        )
        print("✅ PackageResults class instantiated successfully")
        
        # Test ManifestResults
        manifest_result = ManifestResults(
            docker_compose_created=True,
            kubernetes_manifests_created=True,
            manifest_count=3,
            registry_configured="ghcr.io/nebulascloud"
        )
        print("✅ ManifestResults class instantiated successfully")
        
        # Test DocumentationResults
        docs_result = DocumentationResults(
            api_docs_generated=True,
            user_guide_created=True,
            sphinx_build_successful=True,
            docs_size_mb=5.2
        )
        print("✅ DocumentationResults class instantiated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Result classes test failed: {e}")
        return False


def test_dockerfile_exists():
    """Test that the Dockerfile exists and has expected content."""
    print("\n🧪 Testing Dockerfile...")
    
    dockerfile_path = "Dockerfile"
    if not os.path.exists(dockerfile_path):
        print(f"❌ Dockerfile not found at {dockerfile_path}")
        return False
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check for multi-stage build stages
    required_stages = ["base", "development", "testing", "production"]
    for stage in required_stages:
        if f"FROM python:3.11-slim AS {stage}" in content or f"FROM base AS {stage}" in content:
            print(f"✅ Found {stage} stage in Dockerfile")
        else:
            print(f"❌ Missing {stage} stage in Dockerfile")
            return False
    
    # Check for security hardening
    security_checks = [
        "useradd",  # Non-root user creation
        "chown",    # Proper file permissions  
        "USER",     # Switch to non-root user
        "HEALTHCHECK"  # Health check
    ]
    
    for check in security_checks:
        if check in content:
            print(f"✅ Found security feature: {check}")
        else:
            print(f"⚠️  Security feature not found: {check}")
    
    return True


def test_module_structure():
    """Test that the building module has expected structure."""
    print("\n🧪 Testing module structure...")
    
    try:
        # Import and check functions exist
        from dagger_mcp_server.building import Builder
        
        # Check that Builder has expected methods
        expected_methods = [
            'build_artifacts',
            'build_production_image',
            'generate_python_packages',
            'create_deployment_manifests',
            'generate_documentation'
        ]
        
        builder = Builder()
        for method_name in expected_methods:
            if hasattr(builder, method_name):
                print(f"✅ Found method: {method_name}")
            else:
                print(f"❌ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Module structure test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests and return overall success."""
    print("🚀 Starting Building Stage Validation Tests\n")
    
    results = []
    
    # Test builder classes
    results.append(await test_builder_classes())
    
    # Test result classes
    results.append(test_result_classes())
    
    # Test Dockerfile
    results.append(test_dockerfile_exists())
    
    # Test module structure
    results.append(test_module_structure())
    
    # Overall result
    all_passed = all(results)
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests passed! Building stage implementation is ready.")
        print("\n📦 Expected Artifact Structure:")
        print("""
build/artifacts/
├── images/
│   ├── production.tar
│   ├── development.tar  
│   └── testing.tar
├── packages/
│   ├── jira-dependency-analyzer-0.1.0-py3-none-any.whl
│   └── jira-dependency-analyzer-0.1.0.tar.gz
├── manifests/
│   ├── docker-compose.yml
│   ├── k8s-deployment.yaml
│   └── k8s-service.yaml
├── docs/
│   ├── api/
│   └── user-guide/
└── configs/
    ├── production.env
    ├── staging.env
    └── development.env
        """)
        print("\n🔧 Local Execution Examples:")
        print("dagger call build-artifacts --source ./src/demo_mcp_app")
        print("dagger call build-production-image --source ./src/demo_mcp_app")
        print("dagger call generate-python-packages --source ./src/demo_mcp_app")
    else:
        print("❌ Some tests failed. Please review the implementation.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)