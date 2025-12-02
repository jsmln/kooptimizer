"""
Test Runner for Kooptimizer Comprehensive Testing

This script runs all test suites and generates a comprehensive report.

Usage:
    python run_all_tests.py
    python run_all_tests.py --duplication-only
    python run_all_tests.py --functionality-only
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Orchestrates all test executions"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {
            'duplication_detection': None,
            'comprehensive_functionality': None,
            'existing_tests': None
        }
        self.start_time = None
        self.end_time = None
    
    def print_header(self, text):
        """Print a formatted header"""
        print("\n" + "="*80)
        print(f"  {text}")
        print("="*80 + "\n")
    
    def run_duplication_detection(self):
        """Run duplication detection tests"""
        self.print_header("RUNNING DUPLICATION DETECTION TESTS")
        
        try:
            result = subprocess.run(
                [sys.executable, 'test_duplication_detection.py'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            self.results['duplication_detection'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'returncode': result.returncode
            }
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running duplication detection: {e}")
            self.results['duplication_detection'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def run_comprehensive_functionality_tests(self):
        """Run comprehensive functionality tests"""
        self.print_header("RUNNING COMPREHENSIVE FUNCTIONALITY TESTS")
        
        try:
            result = subprocess.run(
                [sys.executable, 'manage.py', 'test', 'test_comprehensive_functionality'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            self.results['comprehensive_functionality'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'returncode': result.returncode
            }
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running functionality tests: {e}")
            self.results['comprehensive_functionality'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def run_existing_tests(self):
        """Run existing test suite"""
        self.print_header("RUNNING EXISTING TESTS")
        
        try:
            # Run all tests in the tests/ directory
            result = subprocess.run(
                [sys.executable, 'manage.py', 'test', 'tests'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            self.results['existing_tests'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'returncode': result.returncode
            }
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running existing tests: {e}")
            self.results['existing_tests'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def generate_summary_report(self):
        """Generate a summary report of all test results"""
        self.print_header("TEST EXECUTION SUMMARY")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r and r.get('success'))
        
        print(f"📊 Total Test Suites: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}\n")
        
        for test_name, result in self.results.items():
            if result:
                status = "✅ PASS" if result.get('success') else "❌ FAIL"
                print(f"{status} - {test_name.replace('_', ' ').title()}")
            else:
                print(f"⏭️  SKIP - {test_name.replace('_', ' ').title()}")
        
        print(f"\n⏱️  Total Execution Time: {(self.end_time - self.start_time).total_seconds():.2f}s")
        
        # Save summary to file
        self.save_summary_report()
        
        return passed_tests == total_tests
    
    def save_summary_report(self):
        """Save summary report to file"""
        report_file = self.project_root / 'TEST_EXECUTION_SUMMARY.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Test Execution Summary\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Overview\n\n")
            total_tests = len(self.results)
            passed_tests = sum(1 for r in self.results.values() if r and r.get('success'))
            
            f.write(f"- Total Test Suites: {total_tests}\n")
            f.write(f"- Passed: {passed_tests}\n")
            f.write(f"- Failed: {total_tests - passed_tests}\n")
            f.write(f"- Execution Time: {(self.end_time - self.start_time).total_seconds():.2f}s\n\n")
            
            f.write("## Test Results\n\n")
            
            for test_name, result in self.results.items():
                f.write(f"### {test_name.replace('_', ' ').title()}\n\n")
                
                if result:
                    if result.get('success'):
                        f.write("**Status:** ✅ PASS\n\n")
                    else:
                        f.write("**Status:** ❌ FAIL\n\n")
                    
                    if 'output' in result:
                        f.write("**Output:**\n```\n")
                        f.write(result['output'][:1000])  # First 1000 chars
                        if len(result['output']) > 1000:
                            f.write("\n... (truncated)")
                        f.write("\n```\n\n")
                    
                    if 'error' in result:
                        f.write(f"**Error:** {result['error']}\n\n")
                else:
                    f.write("**Status:** ⏭️ SKIPPED\n\n")
            
            f.write("## Recommendations\n\n")
            
            if passed_tests == total_tests:
                f.write("✅ All tests passed! The codebase is in good shape.\n\n")
            else:
                f.write("⚠️ Some tests failed. Please review the failures and fix the issues.\n\n")
            
            f.write("### Next Steps\n\n")
            f.write("1. Review failed tests and fix issues\n")
            f.write("2. Address any duplication warnings\n")
            f.write("3. Improve test coverage for untested areas\n")
            f.write("4. Run tests regularly as part of CI/CD pipeline\n")
        
        print(f"\n📄 Summary report saved to: {report_file}")
    
    def run_all(self, duplication_only=False, functionality_only=False):
        """Run all tests"""
        self.start_time = datetime.now()
        
        self.print_header("KOOPTIMIZER COMPREHENSIVE TEST SUITE")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        all_passed = True
        
        if not functionality_only:
            # Run duplication detection first
            if not self.run_duplication_detection():
                all_passed = False
                print("\n⚠️  Duplication detection failed, but continuing with other tests...")
        
        if not duplication_only:
            # Run comprehensive functionality tests
            if not self.run_comprehensive_functionality_tests():
                all_passed = False
                print("\n⚠️  Functionality tests failed, but continuing with other tests...")
            
            # Run existing tests
            if not self.run_existing_tests():
                all_passed = False
                print("\n⚠️  Existing tests failed...")
        
        self.end_time = datetime.now()
        
        # Generate summary
        final_result = self.generate_summary_report()
        
        if final_result:
            self.print_header("✅ ALL TESTS PASSED!")
            return 0
        else:
            self.print_header("❌ SOME TESTS FAILED")
            return 1


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Kooptimizer comprehensive tests')
    parser.add_argument('--duplication-only', action='store_true',
                        help='Run only duplication detection tests')
    parser.add_argument('--functionality-only', action='store_true',
                        help='Run only functionality tests')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    exit_code = runner.run_all(
        duplication_only=args.duplication_only,
        functionality_only=args.functionality_only
    )
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
