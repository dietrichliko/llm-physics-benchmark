#!/usr/bin/env bash
# release.sh — Bump version, generate changelog, commit, tag, and push.
#
# Requires: git-cliff (https://git-cliff.org/), git, python3
#
# Usage:
#   ./scripts/release.sh              # auto-detect bump from conventional commits
#   ./scripts/release.sh patch        # force patch bump  (0.1.0 → 0.1.1)
#   ./scripts/release.sh minor        # force minor bump  (0.1.0 → 0.2.0)
#   ./scripts/release.sh major        # force major bump  (0.1.0 → 1.0.0)

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ── Preflight checks ────────────────────────────────────────────────────────

if ! command -v git-cliff &>/dev/null; then
  echo "error: git-cliff is not installed." >&2
  echo "       Install it from https://git-cliff.org/ (e.g. cargo install git-cliff)" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "error: working directory is not clean. Commit or stash your changes first." >&2
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  echo "warning: you are on branch '$CURRENT_BRANCH', not 'main'."
  read -r -p "Continue anyway? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || exit 1
fi

# ── Determine next version ───────────────────────────────────────────────────

BUMP="${1:-}"

if [[ -n "$BUMP" ]]; then
  # Validate explicit bump type
  if [[ "$BUMP" != "patch" && "$BUMP" != "minor" && "$BUMP" != "major" ]]; then
    echo "error: bump type must be 'patch', 'minor', or 'major' (got '$BUMP')" >&2
    exit 1
  fi

  # Read current version from pyproject.toml and apply bump manually
  CURRENT_VERSION="$(python3 -c "
import re, sys
m = re.search(r'^version = \"([^\"]+)\"', open('pyproject.toml').read(), re.MULTILINE)
print(m.group(1) if m else sys.exit(1))
")"
  IFS='.' read -r MAJOR MINOR PATCH <<<"$CURRENT_VERSION"
  case "$BUMP" in
    major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
    minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
    patch) PATCH=$((PATCH + 1)) ;;
  esac
  NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
else
  # Auto-detect from conventional commits using git-cliff
  BUMPED="$(git-cliff --bumped-version 2>/dev/null || true)"
  if [[ -z "$BUMPED" ]]; then
    echo "error: git-cliff could not determine the next version." >&2
    echo "       Make sure there are conventional commits since the last tag." >&2
    echo "       Or specify a bump type explicitly: ./scripts/release.sh patch" >&2
    exit 1
  fi
  # git-cliff returns "v1.2.3"; strip the leading 'v'
  NEW_VERSION="${BUMPED#v}"
fi

TAG="v${NEW_VERSION}"

echo "Current branch : $CURRENT_BRANCH"
echo "Next version   : $NEW_VERSION  (tag: $TAG)"
read -r -p "Proceed? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || exit 1

# ── Update version in pyproject.toml ────────────────────────────────────────

python3 - "$NEW_VERSION" <<'EOF'
import re, sys
new_ver = sys.argv[1]
path = "pyproject.toml"
content = open(path).read()
updated = re.sub(r'(?m)^version = "[^"]*"', f'version = "{new_ver}"', content)
if updated == content:
    print(f"error: could not find 'version = \"...\"' in {path}", file=sys.stderr)
    sys.exit(1)
open(path, "w").write(updated)
print(f"Updated {path}: version = \"{new_ver}\"")
EOF

# ── Generate / update CHANGELOG.md ──────────────────────────────────────────

echo "Generating CHANGELOG.md with git-cliff ..."
git-cliff --tag "$TAG" -o CHANGELOG.md

# ── Commit, tag, push ────────────────────────────────────────────────────────

git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): prepare for ${TAG}"

git tag -a "$TAG" -m "Release ${TAG}"

echo ""
echo "Created commit and tag $TAG."
read -r -p "Push to origin? [y/N] " push_confirm
if [[ "$push_confirm" =~ ^[Yy]$ ]]; then
  git push origin "$CURRENT_BRANCH"
  git push origin "$TAG"
  echo "Pushed $CURRENT_BRANCH and $TAG to origin."
else
  echo "Not pushed. Run manually:"
  echo "  git push origin $CURRENT_BRANCH && git push origin $TAG"
fi
