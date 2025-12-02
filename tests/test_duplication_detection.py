"""
Duplication Detection Tests for Kooptimizer

This test suite detects and prevents code duplications:
- Duplicate decorator definitions
- Duplicate model definitions  
- Duplicate signal handlers
- Duplicate stored procedures
- Duplicate frontend functions
- Duplicate API endpoints

Run with: python test_duplication_detection.py
"""

import os
import re
import ast
import json
from pathlib import Path
from collections import defaultdict


class DuplicationDetector:
    """Detects code duplications across the codebase"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.info = []
    
    def log_issue(self, category, severity, message, locations):
        """Log a duplication issue"""
        issue = {
            'category': category,
            'severity': severity,
            'message': message,
            'locations': locations
        }
        
        if severity == 'CRITICAL':
            self.issues.append(issue)
        elif severity == 'WARNING':
            self.warnings.append(issue)
        else:
            self.info.append(issue)
    
    def detect_duplicate_decorators(self):
        """Detect duplicate decorator definitions"""
        print("\n🔍 Checking for duplicate decorators...")
        
        decorator_definitions = defaultdict(list)
        
        # Search for decorator definitions in Python files
        for py_file in self.project_root.rglob('apps/**/*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find login_required decorators
                if 'def login_required' in content or 'def login_required_custom' in content:
                    # Parse the file to find the exact definition
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if 'login_required' in node.name:
                                decorator_definitions[node.name].append(str(py_file))
                                
                # Find role_required decorators
                if 'def role_required' in content:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if 'role_required' in node.name:
                                decorator_definitions[node.name].append(str(py_file))
                                
            except Exception as e:
                print(f"  ⚠️  Error parsing {py_file}: {e}")
        
        # Check for duplicates
        for decorator_name, locations in decorator_definitions.items():
            if len(locations) > 1:
                self.log_issue(
                    'Decorators',
                    'CRITICAL',
                    f"Duplicate decorator '{decorator_name}' found in {len(locations)} files",
                    locations
                )
                print(f"  ❌ CRITICAL: '{decorator_name}' defined in {len(locations)} files:")
                for loc in locations:
                    print(f"     - {loc}")
            else:
                print(f"  ✅ '{decorator_name}' is unique")
    
    def detect_duplicate_models(self):
        """Detect duplicate model definitions"""
        print("\n🔍 Checking for duplicate models...")
        
        model_definitions = defaultdict(list)
        
        # Search for model definitions in models.py files
        for models_file in self.project_root.rglob('apps/**/models.py'):
            try:
                with open(models_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Check if it's a Django model
                            for base in node.bases:
                                if hasattr(base, 'attr') and base.attr == 'Model':
                                    model_definitions[node.name].append(str(models_file))
                                elif hasattr(base, 'id') and 'Model' in str(base.id):
                                    model_definitions[node.name].append(str(models_file))
                                    
            except Exception as e:
                print(f"  ⚠️  Error parsing {models_file}: {e}")
        
        # Check for duplicates
        critical_models = ['Admin', 'Staff', 'Officer', 'User', 'Users']
        
        for model_name, locations in model_definitions.items():
            if len(locations) > 1:
                severity = 'CRITICAL' if model_name in critical_models else 'WARNING'
                self.log_issue(
                    'Models',
                    severity,
                    f"Duplicate model '{model_name}' found in {len(locations)} files",
                    locations
                )
                print(f"  ❌ {severity}: Model '{model_name}' defined in {len(locations)} files:")
                for loc in locations:
                    print(f"     - {loc}")
            else:
                if model_name in critical_models:
                    print(f"  ✅ Model '{model_name}' is unique")
    
    def detect_duplicate_signals(self):
        """Detect duplicate signal handlers without dispatch_uid"""
        print("\n🔍 Checking for signal handler duplications...")
        
        signal_handlers = []
        
        # Search for signal handlers in signals.py files
        for signals_file in self.project_root.rglob('apps/**/signals.py'):
            try:
                with open(signals_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Find @receiver decorators
                    receiver_pattern = r'@receiver\((.*?)\)'
                    matches = re.finditer(receiver_pattern, content, re.DOTALL)
                    
                    for match in matches:
                        receiver_args = match.group(1)
                        has_dispatch_uid = 'dispatch_uid' in receiver_args
                        
                        signal_handlers.append({
                            'file': str(signals_file),
                            'args': receiver_args.strip(),
                            'has_dispatch_uid': has_dispatch_uid
                        })
                        
                        if not has_dispatch_uid:
                            self.log_issue(
                                'Signals',
                                'WARNING',
                                f"Signal handler without dispatch_uid in {signals_file}",
                                [str(signals_file)]
                            )
                            print(f"  ⚠️  WARNING: Signal handler without dispatch_uid:")
                            print(f"     - {signals_file}")
                            print(f"     - Args: {receiver_args.strip()}")
                        else:
                            print(f"  ✅ Signal handler has dispatch_uid: {signals_file}")
                            
            except Exception as e:
                print(f"  ⚠️  Error parsing {signals_file}: {e}")
    
    def detect_duplicate_stored_procedures(self):
        """Detect duplicate stored procedure definitions"""
        print("\n🔍 Checking for duplicate stored procedures...")
        
        procedure_definitions = defaultdict(list)
        
        # Search for stored procedures
        stored_proc_dir = self.project_root / 'stored_procedures'
        if stored_proc_dir.exists():
            for sql_file in stored_proc_dir.glob('*.sql'):
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Find CREATE OR REPLACE FUNCTION/PROCEDURE statements
                        pattern = r'CREATE\s+OR\s+REPLACE\s+(FUNCTION|PROCEDURE)\s+(\w+)'
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        
                        for match in matches:
                            proc_type = match.group(1)
                            proc_name = match.group(2)
                            procedure_definitions[proc_name].append(str(sql_file))
                            
                except Exception as e:
                    print(f"  ⚠️  Error parsing {sql_file}: {e}")
        
        # Check for duplicates
        for proc_name, locations in procedure_definitions.items():
            if len(locations) > 1:
                self.log_issue(
                    'Stored Procedures',
                    'WARNING',
                    f"Procedure '{proc_name}' defined in {len(locations)} files (may be intentional)",
                    locations
                )
                print(f"  ⚠️  WARNING: Procedure '{proc_name}' defined in {len(locations)} files:")
                for loc in locations:
                    print(f"     - {loc}")
            else:
                print(f"  ✅ Procedure '{proc_name}' is unique")
    
    def detect_duplicate_frontend_functions(self):
        """Detect duplicate frontend JavaScript functions"""
        print("\n🔍 Checking for duplicate frontend functions...")
        
        function_definitions = defaultdict(list)
        critical_functions = [
            'sendMessage',
            'handleSendCredentials',
            'sendOTP',
            'submitForm'
        ]
        
        # Search for JavaScript/template files
        for template_file in self.project_root.rglob('templates/**/*.html'):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Find function definitions
                    patterns = [
                        r'function\s+(\w+)\s*\(',  # function name()
                        r'const\s+(\w+)\s*=\s*function',  # const name = function
                        r'let\s+(\w+)\s*=\s*function',  # let name = function
                        r'var\s+(\w+)\s*=\s*function',  # var name = function
                        r'async\s+function\s+(\w+)\s*\(',  # async function name()
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            func_name = match.group(1)
                            if func_name in critical_functions:
                                function_definitions[func_name].append(str(template_file))
                                
            except Exception as e:
                print(f"  ⚠️  Error parsing {template_file}: {e}")
        
        # Check for duplicates
        for func_name, locations in function_definitions.items():
            if len(locations) > 1:
                self.log_issue(
                    'Frontend Functions',
                    'WARNING',
                    f"Function '{func_name}' defined in {len(locations)} files",
                    locations
                )
                print(f"  ⚠️  WARNING: Function '{func_name}' defined in {len(locations)} files:")
                for loc in locations:
                    print(f"     - {loc}")
            else:
                print(f"  ✅ Function '{func_name}' is unique")
    
    def detect_duplicate_url_patterns(self):
        """Detect duplicate URL patterns"""
        print("\n🔍 Checking for duplicate URL patterns...")
        
        url_patterns = defaultdict(list)
        
        # Search for urls.py files
        for urls_file in self.project_root.rglob('apps/**/urls.py'):
            try:
                with open(urls_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Find path() declarations
                    pattern = r"path\('([^']+)',"
                    matches = re.finditer(pattern, content)
                    
                    for match in matches:
                        url_path = match.group(1)
                        url_patterns[url_path].append(str(urls_file))
                        
            except Exception as e:
                print(f"  ⚠️  Error parsing {urls_file}: {e}")
        
        # Check for duplicates
        for url_path, locations in url_patterns.items():
            if len(locations) > 1:
                # This is usually okay since they're in different apps
                # But log as info
                self.log_issue(
                    'URL Patterns',
                    'INFO',
                    f"URL pattern '{url_path}' found in {len(locations)} apps",
                    locations
                )
                print(f"  ℹ️  INFO: URL '{url_path}' in {len(locations)} apps (may be namespaced):")
                for loc in locations:
                    print(f"     - {loc}")
    
    def check_guard_flags(self):
        """Check for guard flags in critical functions"""
        print("\n🔍 Checking for guard flags in critical functions...")
        
        critical_files = {
            'templates/communications/message.html': 'isSending',
            'templates/account_management/account_management.html': 'isSendingCredentials',
            'templates/login.html': 'isSubmitting',
        }
        
        for file_path, guard_flag in critical_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        if guard_flag in content:
                            print(f"  ✅ Guard flag '{guard_flag}' found in {file_path}")
                        else:
                            self.log_issue(
                                'Guard Flags',
                                'WARNING',
                                f"Missing guard flag '{guard_flag}' in {file_path}",
                                [str(full_path)]
                            )
                            print(f"  ⚠️  WARNING: Missing guard flag '{guard_flag}' in {file_path}")
                except Exception as e:
                    print(f"  ⚠️  Error reading {file_path}: {e}")
            else:
                print(f"  ℹ️  File not found: {file_path}")
    
    def generate_report(self):
        """Generate a comprehensive duplication report"""
        print("\n" + "="*80)
        print("DUPLICATION DETECTION REPORT")
        print("="*80)
        
        print(f"\n🔴 CRITICAL ISSUES: {len(self.issues)}")
        for issue in self.issues:
            print(f"\n  Category: {issue['category']}")
            print(f"  Message: {issue['message']}")
            print(f"  Locations:")
            for loc in issue['locations']:
                print(f"    - {loc}")
        
        print(f"\n🟡 WARNINGS: {len(self.warnings)}")
        for warning in self.warnings:
            print(f"\n  Category: {warning['category']}")
            print(f"  Message: {warning['message']}")
            print(f"  Locations:")
            for loc in warning['locations']:
                print(f"    - {loc}")
        
        print(f"\n🔵 INFO: {len(self.info)}")
        for info_item in self.info:
            print(f"\n  Category: {info_item['category']}")
            print(f"  Message: {info_item['message']}")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Critical Issues: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Info: {len(self.info)}")
        
        if len(self.issues) > 0:
            print("\n❌ FAIL: Critical duplication issues found!")
            print("Please fix the critical issues before proceeding.")
            return False
        elif len(self.warnings) > 0:
            print("\n⚠️  PASS WITH WARNINGS: Some duplications detected.")
            print("Consider addressing the warnings.")
            return True
        else:
            print("\n✅ PASS: No critical duplications detected!")
            return True
    
    def run_all_checks(self):
        """Run all duplication detection checks"""
        print("="*80)
        print("RUNNING DUPLICATION DETECTION TESTS")
        print("="*80)
        
        self.detect_duplicate_decorators()
        self.detect_duplicate_models()
        self.detect_duplicate_signals()
        self.detect_duplicate_stored_procedures()
        self.detect_duplicate_frontend_functions()
        self.detect_duplicate_url_patterns()
        self.check_guard_flags()
        
        return self.generate_report()


def main():
    """Main entry point"""
    import sys
    
    # Get project root (current directory)
    project_root = os.getcwd()
    
    print(f"Project Root: {project_root}\n")
    
    detector = DuplicationDetector(project_root)
    success = detector.run_all_checks()
    
    # Save report to file
    report_file = Path(project_root) / 'DUPLICATION_DETECTION_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Duplication Detection Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Critical Issues\n\n")
        if detector.issues:
            for issue in detector.issues:
                f.write(f"### {issue['category']}: {issue['message']}\n\n")
                f.write("**Locations:**\n")
                for loc in issue['locations']:
                    f.write(f"- `{loc}`\n")
                f.write("\n")
        else:
            f.write("✅ No critical issues found.\n\n")
        
        f.write("## Warnings\n\n")
        if detector.warnings:
            for warning in detector.warnings:
                f.write(f"### {warning['category']}: {warning['message']}\n\n")
                f.write("**Locations:**\n")
                for loc in warning['locations']:
                    f.write(f"- `{loc}`\n")
                f.write("\n")
        else:
            f.write("✅ No warnings.\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Critical Issues: {len(detector.issues)}\n")
        f.write(f"- Warnings: {len(detector.warnings)}\n")
        f.write(f"- Info: {len(detector.info)}\n\n")
        
        if success:
            f.write("**Status:** ✅ PASS\n")
        else:
            f.write("**Status:** ❌ FAIL\n")
    
    print(f"\n📄 Report saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    from datetime import datetime
    main()
