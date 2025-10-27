# Standup Documentation

## Overview

This directory contains the standup template for building schema-version-confined lab environments.

## Files

### `standup_template.json`
**Purpose**: Greenfield template for standing up any schema version  
**Status**: Template - NOT for direct execution  
**Usage**: Copy and replace `{VERSION}` placeholders when ready to standup a new schema version

## When to Use

### NOT NOW
- We are currently in **cleanup/reset phase**
- Repo contains v0.3.6a code (archived in `meta/archived/`)
- Do not attempt standup until after cleanup

### AFTER CLEANUP
1. Execute `CLEANUP_PLAN.md` steps 1-9 to clean repo
2. Verify MCP tests still pass
3. Repo is now minimal foundation
4. THEN copy `standup_template.json` to `v0_7_3_standup.json`
5. Replace placeholders: `{VERSION}` → `0.7.3`, `{VERSION_UNDERSCORE}` → `0_7_3`
6. Follow standup steps 1-7

## Template Design

The `standup_template.json` is **greenfield-focused**:
- No references to v0.3.6a cleanup
- No backward-looking migration steps
- Pure forward-looking: "Given clean repo, how do we build this?"
- Templated: Works for 0.7.3, 0.7.4, 1.0.0, any future version

## Workflow

```
Current State (v0.3.6a)
    ↓
Execute CLEANUP_PLAN.md
    ↓
Minimal Foundation
    ↓
Instantiate standup_template.json for 0.7.3
    ↓
Execute v0_7_3_standup.json steps 1-7
    ↓
Working 0.7.3 Generator
    ↓
(Future) Instantiate standup_template.json for 0.7.4
    ↓
Execute v0_7_4_standup.json steps 1-7
    ↓
Parallel 0.7.3 + 0.7.4 Support
```

## Key Principle

**Standup is greenfield**, not migration.

The template assumes:
- Clean repo with MCP infrastructure
- No existing generators
- No version-specific code yet
- Pure TDD from scratch

This makes it reusable for any schema version, forever.

