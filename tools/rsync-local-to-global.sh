#!/usr/bin/env bash

rsync -av \
  --exclude='.DS_Store' \
  --exclude='__pycache__/' \
  ./.claude/commands/ ~/.claude/commands/

rsync -av \
  --exclude='.DS_Store' \
  --exclude='__pycache__/' \
  ./.claude/skills/ ~/.claude/skills/
