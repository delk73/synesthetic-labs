# Standup Documentation

## Overview

This directory contains standup templates and scripts for building schema-version-confined lab environments.

## Files

### `standup_template.json`
**Purpose**: Greenfield template for standing up any schema version  
**Status**: Template - NOT for direct execution  
**Usage**: Copy and replace `{VERSION}` placeholders when ready to standup a new schema version

### `v2standup.json` (Legacy)
**Purpose**: Historical v0.3.6a → v2 migration plan  
**Status**: Backward-looking, references v0.3.6a cleanup  
**Usage**: Reference for lessons learned, not for greenfield standup

### `reset.json`
**Purpose**: Reset procedure to strip v0.3.6a cruft  
**Status**: One-time cleanup script  
**Usage**: Execute once to prepare repo for fresh standup

## When to Use

### NOT NOW
- We are currently in **documentation phase**
- Repo contains v0.3.6a code (archived in `meta/archived/`)
- Reset has not been executed yet
- Do not attempt standup until after reset

### AFTER RESET
1. Execute `reset.json` procedure to clean repo
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
Execute reset.json
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
