#!/usr/bin/env bash
# Package Desk420 as a signed macOS .app bundle (and optionally a drag-to-Applications .dmg).
#
# Usage:
#   ./scripts/package_macos.sh                # build debug Desk420.app
#   ./scripts/package_macos.sh --release      # build release Desk420.app
#   ./scripts/package_macos.sh --release --dmg # also build target/release/Desk420.dmg
set -euo pipefail

cd "$(dirname "$0")/.."

MODE="debug"
CPC_FLAGS=()
MAKE_DMG=0

for arg in "$@"; do
    case "$arg" in
        --release)
            MODE="release"
            CPC_FLAGS+=(--release)
            ;;
        --debug)
            MODE="debug"
            ;;
        --dmg)
            MAKE_DMG=1
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 2
            ;;
    esac
done

if [ -x ./cpc ]; then
    CPC="./cpc"
elif command -v cpc >/dev/null 2>&1; then
    CPC="$(command -v cpc)"
else
    echo "error: could not find 'cpc' (neither ./cpc nor on PATH)" >&2
    exit 1
fi

if [ ! -f assets/AppIcon.icns ]; then
    python3 scripts/make_icon.py
fi

echo "==> Packaging Desk420.app ($MODE) using $CPC..."
if [ "$MODE" = "release" ]; then
    "$CPC" package --release
else
    "$CPC" package
fi

APP="target/${MODE}/Desk420.app"
if [ ! -d "$APP" ]; then
    echo "error: expected bundle at $APP" >&2
    exit 1
fi

# Verify plist, icon, and code signature.
plutil -lint "$APP/Contents/Info.plist"
if [ ! -f "$APP/Contents/Resources/AppIcon.icns" ]; then
    echo "error: AppIcon.icns missing from $APP/Contents/Resources/" >&2
    exit 1
fi
codesign --verify --deep --strict "$APP"
echo "==> Verified $APP (Info.plist, AppIcon.icns, codesign OK)"

if [ "$MAKE_DMG" -eq 1 ]; then
    DMG="target/${MODE}/Desk420.dmg"
    STAGE="$(mktemp -d)"
    trap 'rm -rf "$STAGE"' EXIT
    cp -R "$APP" "$STAGE/Desk420.app"
    ln -s /Applications "$STAGE/Applications"
    rm -f "$DMG"
    hdiutil create \
        -volname "Desk420" \
        -srcfolder "$STAGE" \
        -ov \
        -format UDZO \
        "$DMG" >/dev/null
    echo "==> Created $DMG ($(du -h "$DMG" | awk '{print $1}'))"
fi
