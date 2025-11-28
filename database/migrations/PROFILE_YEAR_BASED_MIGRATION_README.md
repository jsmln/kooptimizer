# Profile Data Year-Based Migration

## Overview
This migration converts the `profile_data` table from a one-to-one relationship (one profile per cooperative) to a year-based system (one profile per cooperative per year), similar to the `financial_data` table structure.

## Changes Required

### 1. Database Schema Changes

Run the SQL migration script: `database/migrations/add_report_year_to_profile_data.sql`

This script will:
- Drop the unique constraint on `coop_id` (allowing multiple profiles per cooperative)
- Add `report_year` column (integer, nullable)
- Set existing records to current year
- Add unique constraint on `(coop_id, report_year)` to prevent duplicates per year
- Add indexes for performance

### 2. Model Changes

The `ProfileData` model has been updated:
- Changed from `OneToOneField` to `ForeignKey` (allows multiple profiles)
- Added `report_year` field (IntegerField, nullable)
- Updated `Meta.unique_together` to `[['coop', 'report_year']]`

### 3. View Changes

The views have been updated to:
- Query profiles by `report_year` (defaults to current year)
- Prevent editing of past years (only current year and future years are editable)
- Support year parameter in URLs for viewing/editing specific years
- Get profile history (latest 3 years) similar to financial history

### 4. Business Logic

**Editable Years:**
- Current year (year >= current year): ✅ Editable
- Past years (year < current year): ❌ Not editable (read-only)

**Default Behavior:**
- When viewing profile, shows current year's profile by default
- If no profile exists for current year, shows latest available profile
- Year can be specified via `?year=YYYY` query parameter

### 5. Form Updates Needed

The profile form template needs to be updated to:
- Add year selector dropdown (similar to financial history)
- Show profile history cards (latest 3 years)
- Disable form fields when viewing/editing past years
- Display "View Only" message for past years

## Testing Checklist

- [ ] Run database migration script
- [ ] Verify existing profiles have `report_year` set
- [ ] Test creating new profile for current year
- [ ] Test editing current year profile
- [ ] Test viewing past year profile (should be read-only)
- [ ] Test attempting to edit past year (should be blocked)
- [ ] Test year selector in form
- [ ] Test profile history display
- [ ] Test attachment downloads with year parameter
- [ ] Test print profile with year parameter

## Rollback Plan

If issues occur, you can rollback by:
1. Restoring the unique constraint: `CREATE UNIQUE INDEX profile_data_coop_id_key ON profile_data(coop_id);`
2. Removing `report_year` column: `ALTER TABLE profile_data DROP COLUMN report_year;`
3. Reverting model to `OneToOneField`

However, this will lose year-based data, so backup first!

