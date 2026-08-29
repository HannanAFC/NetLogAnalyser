#!/usr/bin/env bash
set -euo pipefail

# NetLogAnalyser self-host installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/HannanAFC/NetLogAnalyser/main/selfhost/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- v1.0.0              # pin to a release tag
#   curl -fsSL .../install.sh | bash -s -- v1.0.0 ~/apps/nla   # custom install dir
#   curl -fsSL .../install.sh | bash -s -- main                # track development branch
#
# Safe to re-run: fetched files are only replaced if their content actually
# changed (the previous copy is kept as a .bak), .env is never touched if it
# already exists (that guard lives in setup.sh), and the image tag written
# into .env is always synced to match whatever ref is asked for.
REPO="HannanAFC/NetLogAnalyser"

REF="${1:-latest}"
INSTALL_DIR="${2:-netloganalyser}"

RAW_BASE="https://raw.githubusercontent.com/${REPO}"
API_BASE="https://api.github.com/repos/${REPO}"
FILES=("docker-compose.selfhost.yml" ".env.example" "setup.sh")

require() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "Missing required command: $1" >&2
		exit 1
	}
}

require curl
require docker

if ! docker compose version >/dev/null 2>&1; then
	echo "docker compose (the v2 plugin) is required but wasn't found." >&2
	echo "See: https://docs.docker.com/compose/install/" >&2
	exit 1
fi

# Resolve "latest" to an actual release tag so we fetch a compose file that
# matches a real, tagged set of GHCR images rather than an in-progress branch.
if [ "$REF" = "latest" ]; then
	echo "Resolving latest release..."
	REF=$(curl -fsSL "${API_BASE}/releases/latest" \
		| grep -m1 '"tag_name"' \
		| sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')
	if [ -z "$REF" ]; then
		echo "Warning: could not resolve a release tag, falling back to main." >&2
		REF="main"
	fi
fi

# Only actual release tags (v1.0.0) have a matching GHCR image tag - the
# release workflow doesn't push images for arbitrary branches. If someone
# explicitly asks for "main" (or any other non-release ref), still fetch the
# compose file from that ref, but pull the :latest images rather than a tag
# that doesn't exist.
if [[ "$REF" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.]+)?$ ]]; then
	IMAGE_TAG="$REF"
else
	echo "Note: '${REF}' has no matching released image - using the :latest image tag."
	IMAGE_TAG="latest"
fi

echo "Installing NetLogAnalyser (${REF}) into ./${INSTALL_DIR}"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Fetch a file from selfhost/ at the resolved ref. Only overwrites the local
# copy if the content is actually different, and backs up the previous
# version first - so a rerun against the same ref does nothing, and a
# rerun against a newer ref doesn't change things without a trace.
fetch() {
	local file="$1" tmp
	tmp="$(mktemp)"

	if ! curl -fsSL "${RAW_BASE}/${REF}/selfhost/${file}" -o "$tmp"; then
		echo "Failed to download selfhost/${file} at ref '${REF}'." >&2
		echo "Check that the ref exists: ${RAW_BASE}/${REF}/selfhost/${file}" >&2
		rm -f "$tmp"
		exit 1
	fi

	if [ -f "$file" ] && cmp -s "$tmp" "$file"; then
		rm -f "$tmp"
		return
	fi

	if [ -f "$file" ]; then
		echo "  ${file} changed - previous copy saved as ${file}.bak"
		cp "$file" "${file}.bak"
	else
		echo "  ${file}"
	fi
	mv "$tmp" "$file"
}

echo "Fetching stack files..."
for f in "${FILES[@]}"; do
	fetch "$f"
done
chmod +x setup.sh

echo ""
NLA_IMAGE_TAG="$IMAGE_TAG" ./setup.sh