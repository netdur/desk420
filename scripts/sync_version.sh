#!/usr/bin/env bash
# Keep Cplus.toml, src/version.cplus, and macos/Info.plist in lockstep.
#
# Usage:
#   ./scripts/sync_version.sh           # sync src/version.cplus & Info.plist from Cplus.toml
#   ./scripts/sync_version.sh 0.1.4     # bump Cplus.toml to 0.1.4, sync others, increment CFBundleVersion
set -euo pipefail

cd "$(dirname "$0")/.."

BUMP=0
if [[ $# -ge 1 ]]; then
    NEW_VER="$1"
    [[ "$NEW_VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
        echo "error: expected semver X.Y.Z, got '$NEW_VER'" >&2
        exit 2
    }
    python3 -c '
import re, sys
p, v = "Cplus.toml", sys.argv[1]
s = open(p).read()
s2, n = re.subn(r"(^version\s*=\s*\")[^\"]+(\")", lambda m: m.group(1) + v + m.group(2), s, count=1, flags=re.M)
assert n == 1, "version line not found in Cplus.toml"
open(p, "w").write(s2)
' "$NEW_VER"
    BUMP=1
fi

VER="$(sed -n 's/^version *= *"\(.*\)"/\1/p' Cplus.toml | head -1)"
[[ -n "$VER" ]] || { echo "error: could not read version from Cplus.toml" >&2; exit 1; }

python3 -c '
import re, sys
v, bump = sys.argv[1], sys.argv[2] == "1"

# 1. src/version.cplus
p = "src/version.cplus"
s = open(p).read()
s2, n = re.subn(r"(^const VERSION: str = \")[^\"]+(\";)", lambda m: m.group(1) + v + m.group(2), s, count=1, flags=re.M)
assert n == 1, "const VERSION not found in src/version.cplus"
if s2 != s:
    open(p, "w").write(s2)

# 2. macos/Info.plist (preserve comments and indentation)
p = "macos/Info.plist"
s = open(p).read()
s2, n1 = re.subn(
    r"(<key>CFBundleShortVersionString</key>\s*<string>)[^<]+(</string>)",
    lambda m: m.group(1) + v + m.group(2),
    s,
    count=1,
)
assert n1 == 1, "CFBundleShortVersionString not found in macos/Info.plist"
if bump:
    s2, n2 = re.subn(
        r"(<key>CFBundleVersion</key>\s*<string>)([0-9]+)(</string>)",
        lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3),
        s2,
        count=1,
    )
    assert n2 == 1, "CFBundleVersion not found in macos/Info.plist"
if s2 != s:
    open(p, "w").write(s2)
' "$VER" "$BUMP"

echo "Synced Desk420 version -> $VER"
