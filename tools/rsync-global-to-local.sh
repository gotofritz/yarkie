#!/usr/bin/env bash

  rsync -av \
    --exclude='.DS_Store' \
    --exclude='debug/' \
    --exclude='file-history/' \
    --exclude='projects/' \
    --exclude='session-env/' \
    --exclude='shell-snapshots/' \
    --exclude='statsig/' \
    --exclude='todos/' \
    --exclude='ide/' \
    --exclude='plugins/' \
    --exclude='history.jsonl' \
    ~/.claude/ ./.claude/
