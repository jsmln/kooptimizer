# Test Execution Summary

**Generated:** 2025-12-01 17:16:34

## Overview

- Total Test Suites: 3
- Passed: 0
- Failed: 3
- Execution Time: 59.94s

## Test Results

### Duplication Detection

**Status:** ❌ FAIL

**Output:**
```
Project Root: C:\Users\Noe Gonzales\Downloads\System\Kooptimizer

================================================================================
RUNNING DUPLICATION DETECTION TESTS
================================================================================

```

### Comprehensive Functionality

**Status:** ❌ FAIL

**Output:**
```
Found 55 test(s).
Type 'yes' if you would like to try deleting the test database 'test_kooptimizer_db2', or 'no' to cancel: 
```

### Existing Tests

**Status:** ❌ FAIL

**Output:**
```

================================================================================
  TEST 1: Does account_management view clear or modify session?
================================================================================

[TEST] Session BEFORE calling account_management view:
SUCCESS! Row data:
Number of columns: 15
Column 0: int = 35
Column 1: str = Test Email Announcement
Column 2: str = This is another email announcement, to check if it allows sending attachments.
Column 3: str = e-mail
Column 4: str = sent
Column 5: str = cooperative
Column 6: datetime = 2025-11-19 16:21:00+00:00
Column 7: datetime = 2025-11-19 15:16:58.010569+00:00
Column 8: int = 33763
Column 9: str = Gemini_Generated_Image_37s4a237s4a237s4.jpg; FAM - Code Reviewer.docx; SIA - Midterm Reviewer.jpg
Column 10: str = [{"attachment_id" : 6, "filename" : "Gemini_Generated_Image_37s4a237s4a237s4.jpg; FAM - Code Reviewer.docx; SIA - Midterm Reviewer.jpg", "original_filename" : "Gemini_Generated_Image_37s4a237s4a23
... (truncated)
```

## Recommendations

⚠️ Some tests failed. Please review the failures and fix the issues.

### Next Steps

1. Review failed tests and fix issues
2. Address any duplication warnings
3. Improve test coverage for untested areas
4. Run tests regularly as part of CI/CD pipeline
