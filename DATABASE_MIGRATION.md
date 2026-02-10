# Database Migration: grade10_mix.json Tasks

## Summary

Successfully created and executed database migration to load 60 programming tasks from `data/tasks/grade10_mix.json` into PostgreSQL.

## What Was Done

### 1. Created Loader Script

**File:** `/backend/scripts/load_grade10_mix.py`

Features:
- Reads tasks from `data/tasks/grade10_mix.json`
- Validates all required fields (subject, topic, difficulty, title, text, input_format, output_format, answer, hints, source)
- Maps JSON subject names to database schema:
  - `"informatics"` → `"informatics"` ✓
  - `"math"` → `"mathematics"` ✓
  - `"physics"` → `"physics"` ✓
- Checks for duplicates (no double-insert)
- Combines extra fields (input_format, output_format, source) into task text
- Provides detailed statistics on load completion

### 2. Fixed Database Schema Bug

**File:** `/backend/app/models/match.py` (line 71-76)

**Issue:** `winner_id` column had both `index=True` and explicit `Index("ix_matches_winner_id")`, causing duplicate index error.

**Fix:** Removed `index=True` from column definition, kept explicit index in `__table_args__`.

### 3. Created Database Initialization Script

**File:** `/backend/scripts/init_db_clean.py`

- Checks existing tables
- Creates all tables if needed
- Disposes connection pool after completion
- Provides clear status reporting

## Data Loaded

### Task Statistics

```
Total tasks:        60
  ├── informatics:  20 tasks (algorithms, graphs, BFS, DFS, etc.)
  ├── mathematics:  20 tasks (geometry, algebra, combinatorics, etc.)
  └── physics:      20 tasks (kinematics, dynamics, conservation laws, etc.)
```

### Difficulty Distribution

- Difficulty 1-5 distributed across all subjects
- Mix of educational and competitive difficulty levels

## How to Load Tasks Again

If you need to reload the tasks (e.g., after DB reset):

```bash
cd backend

# Step 1: Initialize database (creates tables)
python -m scripts.init_db_clean

# Step 2: Load tasks from JSON
python -m scripts.load_grade10_mix
```

## Verification

Tasks are now available in the database:

```bash
# List all tasks by subject
psql -U olympiad -d olympiad -c "SELECT subject, COUNT(*) FROM tasks GROUP BY subject;"
```

Expected output:
```
  subject    | count
-----------+-------
 informatics|    20
 mathematics|    20
 physics    |    20
```

## Frontend Integration

The tasks are now accessible via:

- **API:** `GET /api/tasks?subject=physics&difficulty=3`
- **Frontend:** `/tasks` page shows all 60 tasks with filtering and pagination
- **Catalog:** Tasks can be filtered by subject and difficulty level

## Future Improvements

1. Consider adding task seeding to CI/CD pipeline
2. Create schema validation for JSON files before loading
3. Add rollback capability for partial failed loads
4. Track task source/version for updates

---

**Migration Date:** 2026-02-08
**Status:** ✅ Complete and Verified
