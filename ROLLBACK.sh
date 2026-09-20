#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET=${1:-"$ROOT/settings.json"}
[ "$TARGET" != "$ROOT/.verification/baseline-settings.json" ] || exit 1
ACTUAL=$(shasum -a 256 "$ROOT/.verification/baseline-settings.json" | awk '{print $1}')
[ "$ACTUAL" = "847680ad10fe87326a1791505ba20a877829828b3a4da00fd89f212359b89e81" ] || { echo 'Baseline hash mismatch' >&2; exit 1; }
if [ -f "$TARGET" ]; then
 BACKUP=$(mktemp "${TARGET}.before-rollback.XXXXXX")
 cp -p "$TARGET" "$BACKUP"
fi
cp "$ROOT/.verification/baseline-settings.json" "$TARGET"
cmp -s "$ROOT/.verification/baseline-settings.json" "$TARGET"
echo 'PASS rollback: connector disabled; credentials retained'
