#!/bin/sh
# Build the asciifyy .deb from this checkout.
#
#   packaging/debian/build-deb.sh [OUTPUT_DIR]     (default: dist)
#
# Needs only dpkg-deb and gzip. The package installs the asciify module for the
# system python3 and uses Debian's python3-pil, so it pulls nothing from PyPI.
set -eu

root=$(cd "$(dirname "$0")/../.." && pwd)
out=${1:-$root/dist}
pkg=asciifyy
version=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$root/src/asciify/__init__.py")
[ -n "$version" ] || { echo "build-deb: could not read __version__" >&2; exit 1; }

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
chmod 755 "$stage"

lib="$stage/usr/lib/python3/dist-packages/asciify"
doc="$stage/usr/share/doc/$pkg"
install -d -m 755 "$stage/DEBIAN" "$stage/usr/bin" "$lib" "$stage/usr/share/man/man1" "$doc"

install -m 644 "$root"/src/asciify/*.py "$lib/"

cat > "$stage/usr/bin/asciify" <<'EOF'
#!/usr/bin/python3
import sys

from asciify.cli import main

sys.exit(main())
EOF
chmod 755 "$stage/usr/bin/asciify"

gzip -9n -c "$root/man/asciify.1" > "$stage/usr/share/man/man1/asciify.1.gz"
gzip -9n -c "$root/CHANGELOG.md" > "$doc/changelog.gz"
chmod 644 "$stage/usr/share/man/man1/asciify.1.gz" "$doc/changelog.gz"

{
  echo "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"
  echo "Upstream-Name: asciify"
  echo "Source: https://github.com/markmysler/asciify"
  echo
  echo "Files: *"
  echo "Copyright: 2025 Mark Mysler"
  echo "License: MIT"
  sed 's/^$/./; s/^/ /' "$root/LICENSE"
} > "$doc/copyright"
chmod 644 "$doc/copyright"

size=$(du -sk "$stage/usr" | cut -f1)
cat > "$stage/DEBIAN/control" <<EOF
Package: $pkg
Version: $version
Section: graphics
Priority: optional
Architecture: all
Depends: python3 (>= 3.9), python3-pil
Provides: asciify
Installed-Size: $size
Maintainer: Mark Mysler <myslermark@gmail.com>
Homepage: https://github.com/markmysler/asciify
Description: convert images to ASCII art or colored block art in the terminal
 asciify turns images (PNG, JPEG, GIF, WebP and anything else Pillow can
 read) into ASCII art or 24-bit colored half-block art. It fits the output
 to the terminal, plays animated GIFs, reads files, URLs or standard input,
 and can save the result as text or as an HTML page.
EOF

# Byte-compile on install and clean up on removal, like Debian's own Python packages
cat > "$stage/DEBIAN/postinst" <<EOF
#!/bin/sh
set -e
if [ "\$1" = configure ] && command -v py3compile >/dev/null 2>&1; then
  py3compile -p $pkg
fi
EOF
cat > "$stage/DEBIAN/prerm" <<EOF
#!/bin/sh
set -e
if command -v py3clean >/dev/null 2>&1; then
  py3clean -p $pkg
else
  find /usr/lib/python3/dist-packages/asciify -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
fi
EOF
chmod 644 "$stage/DEBIAN/control"
chmod 755 "$stage/DEBIAN/postinst" "$stage/DEBIAN/prerm"

mkdir -p "$out"
dpkg-deb --root-owner-group --build "$stage" "$out/${pkg}_${version}_all.deb"
