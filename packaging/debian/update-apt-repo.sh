#!/bin/sh
# Add .deb files to a signed apt repository and regenerate its indexes.
#
#   packaging/debian/update-apt-repo.sh REPO_DIR PACKAGE.deb...
#
# REPO_DIR is the root that gets served (the gh-pages branch in CI). Earlier
# versions already in its pool are kept. Signs with the default GnuPG secret
# key, or with $APT_KEY_ID when set. Needs apt-ftparchive (apt-utils) and gpg.
set -eu

[ $# -ge 2 ] || { echo "usage: $0 REPO_DIR PACKAGE.deb..." >&2; exit 2; }
repo=$1
shift

archs="amd64 arm64 armhf i386 ppc64el riscv64 s390x"
pool="$repo/pool/main/a/asciifyy"
mkdir -p "$pool"
for deb in "$@"; do
  cp "$deb" "$pool/"
done

key_args=""
if [ -n "${APT_KEY_ID:-}" ]; then
  key_args="--local-user $APT_KEY_ID"
fi

cd "$repo"
dists=dists/stable
rm -rf "$dists"
for arch in $archs; do
  # The package is Architecture: all, so every architecture lists the same file
  dir="$dists/main/binary-$arch"
  mkdir -p "$dir"
  apt-ftparchive packages pool > "$dir/Packages"
  gzip -9n -k "$dir/Packages"
done

apt-ftparchive \
  -o APT::FTPArchive::Release::Origin=asciify \
  -o APT::FTPArchive::Release::Label=asciify \
  -o APT::FTPArchive::Release::Suite=stable \
  -o APT::FTPArchive::Release::Codename=stable \
  -o APT::FTPArchive::Release::Architectures="$archs" \
  -o APT::FTPArchive::Release::Components=main \
  -o APT::FTPArchive::Release::Description="asciify packages" \
  release "$dists" > Release.tmp
mv Release.tmp "$dists/Release"

# shellcheck disable=SC2086
gpg --batch --yes $key_args --clearsign --output "$dists/InRelease" "$dists/Release"
# shellcheck disable=SC2086
gpg --batch --yes $key_args --armor --detach-sign --output "$dists/Release.gpg" "$dists/Release"

# The public key users download (binary, ready for /etc/apt/keyrings)
# shellcheck disable=SC2086
gpg --batch --yes --export ${APT_KEY_ID:-} > asciify-archive-keyring.gpg
touch .nojekyll

cat > index.html <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>asciify apt repository</title></head>
<body style="font-family: sans-serif; max-width: 48em; margin: 2em auto; padding: 0 1em">
<h1>asciify apt repository</h1>
<p>Install <a href="https://github.com/markmysler/asciify">asciify</a> on Debian or Ubuntu:</p>
<pre>
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://markmysler.github.io/asciify/asciify-archive-keyring.gpg | sudo tee /etc/apt/keyrings/asciify.gpg &gt;/dev/null
echo "deb [signed-by=/etc/apt/keyrings/asciify.gpg] https://markmysler.github.io/asciify stable main" | sudo tee /etc/apt/sources.list.d/asciify.list
sudo apt-get update
sudo apt-get install asciifyy
</pre>
</body>
</html>
EOF
