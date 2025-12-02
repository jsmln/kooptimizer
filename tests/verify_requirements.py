"""
Requirements Verification and Auto-Fix Script
==============================================

This script verifies that all required packages from requirements.txt are installed
and offers to install any missing packages automatically.

Usage:
    python verify_requirements.py          # Check and optionally install missing packages
    python verify_requirements.py --fix    # Automatically install missing packages
"""

import subprocess
import sys
import os
from pathlib import Path


def get_installed_packages():
    """Get a dictionary of installed packages and their versions."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        packages = json.loads(result.stdout)
        return {pkg['name'].lower(): pkg['version'] for pkg in packages}
    except Exception as e:
        print(f"Error getting installed packages: {e}")
        return {}


def parse_requirements(requirements_file):
    """Parse requirements.txt and extract package names."""
    packages = []
    try:
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Extract package name (before ==, >=, etc.)
                package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                if package_name:
                    packages.append((package_name, line))
    except FileNotFoundError:
        print(f"Error: {requirements_file} not found!")
        sys.exit(1)
    
    return packages


def verify_and_fix(auto_fix=False):
    """Verify installed packages and optionally fix missing ones."""
    base_dir = Path(__file__).resolve().parent
    requirements_file = base_dir / 'requirements.txt'
    
    print("="*70)
    print("Kooptimizer Requirements Verification")
    print("="*70)
    print(f"Python executable: {sys.executable}")
    print(f"Requirements file: {requirements_file}")
    print()
    
    # Get installed packages
    print("Checking installed packages...")
    installed = get_installed_packages()
    print(f"Found {len(installed)} installed packages")
    print()
    
    # Parse requirements
    required = parse_requirements(requirements_file)
    print(f"Found {len(required)} required packages")
    print()
    
    # Check for missing packages
    missing = []
    for package_name, requirement_line in required:
        # Normalize package name for comparison
        normalized_name = package_name.lower().replace('_', '-')
        
        # Check various forms of the package name
        found = False
        for installed_name in installed.keys():
            if installed_name.replace('_', '-') == normalized_name:
                found = True
                break
        
        if not found:
            missing.append((package_name, requirement_line))
    
    # Report results
    if not missing:
        print("✓ All required packages are installed!")
        print("="*70)
        return True
    
    print("⚠ Missing packages detected:")
    print("-"*70)
    for package_name, _ in missing:
        print(f"  - {package_name}")
    print("-"*70)
    print()
    
    # Offer to install missing packages
    if auto_fix:
        install = True
    else:
        response = input("Would you like to install missing packages now? (y/n): ")
        install = response.lower() in ['y', 'yes']
    
    if install:
        print("\nInstalling missing packages...")
        print("="*70)
        try:
            # Install from requirements.txt to get correct versions
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                check=True
            )
            print("="*70)
            print("✓ All packages installed successfully!")
            print("="*70)
            return True
        except subprocess.CalledProcessError as e:
            print("="*70)
            print(f"✗ Error installing packages: {e}")
            print("="*70)
            print("\nPlease try manually:")
            print(f"  pip install -r {requirements_file}")
            return False
    else:
        print("\nTo install missing packages manually, run:")
        print(f"  pip install -r {requirements_file}")
        print("\nOr install specific packages:")
        for _, requirement_line in missing:
            print(f"  pip install {requirement_line}")
        print("="*70)
        return False


if __name__ == "__main__":
    auto_fix = '--fix' in sys.argv or '-f' in sys.argv
    
    try:
        success = verify_and_fix(auto_fix)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
