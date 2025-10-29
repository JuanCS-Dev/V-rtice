# How to Create Release v1.0.0

This guide explains how to create the first public release of Vértice-MAXIMUS.

---

## Prerequisites

1. ✅ All changes committed to `main` branch
2. ✅ Repository is **public** (or ready to be made public)
3. ✅ CHANGELOG.md is up to date
4. ✅ All tests passing
5. ✅ Security audit complete (0 secrets found)
6. ✅ Documentation complete

---

## Option 1: Create Release via GitHub CLI (Recommended)

### Step 1: Ensure you're on latest main
```bash
cd /home/maximus/Documentos/V-rtice
git checkout main
git pull origin main
```

### Step 2: Create and push tag
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0 - Awakening 🧬

First public release of Vértice-MAXIMUS.
World's first autonomous cybersecurity platform with biological immune system architecture.

Key Features:
- 125+ microservices (immune cells)
- 99.73% test coverage
- 574+ unit tests
- MAXIMUS AI consciousness
- Multi-LLM support (Claude, OpenAI, Gemini)
- NEUROSHELL natural language interface
- Apache 2.0 license
- Comprehensive legal compliance (US, Brazil, EU)

See RELEASE_v1.0.0.md for full release notes."

# Push tag to GitHub
git push origin v1.0.0
```

### Step 3: Create release with notes
```bash
# Create release using prepared notes
gh release create v1.0.0 \
  --title "v1.0.0 - Awakening 🧬" \
  --notes-file RELEASE_v1.0.0.md \
  --latest \
  --verify-tag
```

### Step 4: (Optional) Upload assets
If you want to attach build artifacts:
```bash
gh release upload v1.0.0 \
  dist/vertice-maximus-1.0.0.tgz \
  docker-images/vertice-complete-1.0.0.tar.gz
```

---

## Option 2: Create Release via GitHub Web Interface

### Step 1: Push tag
```bash
cd /home/maximus/Documentos/V-rtice
git checkout main
git pull origin main

# Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0 - Awakening"
git push origin v1.0.0
```

### Step 2: Navigate to Releases page
1. Go to https://github.com/JuanCS-Dev/V-rtice
2. Click "Releases" (right sidebar)
3. Click "Draft a new release"

### Step 3: Fill out release form
- **Choose a tag**: Select `v1.0.0` (or create it)
- **Release title**: `v1.0.0 - Awakening 🧬`
- **Description**: Copy content from `RELEASE_v1.0.0.md`
- **Set as latest release**: ✅ Check this
- **Create a discussion for this release**: ✅ Check this (if Discussions enabled)

### Step 4: (Optional) Attach binaries
- Drag and drop build artifacts if you have them
- Examples: Docker images, npm tarballs, compiled binaries

### Step 5: Publish
- Click "Publish release"

---

## Option 3: Automated Release (Future Setup)

For automated releases with semantic-release:

### Install semantic-release
```bash
npm install --save-dev semantic-release \
  @semantic-release/changelog \
  @semantic-release/git \
  @semantic-release/github
```

### Configure .releaserc.json
```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    "@semantic-release/github",
    "@semantic-release/git"
  ]
}
```

### Trigger release
```bash
npx semantic-release
```

---

## Post-Release Checklist

After creating the release:

### 1. Verify Release
- [ ] Release appears on https://github.com/JuanCS-Dev/V-rtice/releases
- [ ] Tag `v1.0.0` is visible
- [ ] Release notes are complete and formatted correctly
- [ ] "Latest" badge is showing

### 2. Update CHANGELOG.md
```bash
# Update CHANGELOG to mark v1.0.0 as released
# Change: ## [Unreleased]
# To:     ## [1.0.0] - 2025-MM-DD
vim CHANGELOG.md
git add CHANGELOG.md
git commit -m "docs: Mark v1.0.0 as released in CHANGELOG"
git push origin main
```

### 3. Announce Release
- [ ] Tweet announcement on Twitter/X
- [ ] Post on LinkedIn
- [ ] Submit to Hacker News (Show HN)
- [ ] Post on Reddit (r/cybersecurity, r/netsec, r/opensource)
- [ ] Post on Dev.to
- [ ] Update landing page if needed

### 4. Monitor
- [ ] Watch for issues reported
- [ ] Respond to questions/comments
- [ ] Monitor GitHub stars/forks
- [ ] Check npm download stats (if published)

### 5. npm Package (if applicable)
If you want to publish to npm:
```bash
# Update package.json version
npm version 1.0.0

# Publish to npm
npm publish

# Or for scoped package
npm publish --access public
```

---

## Troubleshooting

### Error: "tag already exists"
```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag (if pushed)
git push origin :refs/tags/v1.0.0

# Recreate tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Error: "gh: command not found"
```bash
# Install GitHub CLI
# Ubuntu/Debian:
sudo apt install gh

# macOS:
brew install gh

# Authenticate
gh auth login
```

### Error: "permission denied" when creating release
```bash
# Re-authenticate with correct permissions
gh auth login --scopes repo,write:packages
```

---

## Release Checklist Summary

Before creating release:
- [ ] All changes committed and pushed to main
- [ ] CHANGELOG.md updated with all changes
- [ ] RELEASE_v1.0.0.md prepared
- [ ] All tests passing (574+ tests, 99.73% coverage)
- [ ] Security audit complete (0 secrets)
- [ ] Documentation complete and up to date
- [ ] README.md reviewed and polished
- [ ] Repository is public (or ready to be)

Creating release:
- [ ] Create tag v1.0.0
- [ ] Push tag to GitHub
- [ ] Create release with prepared notes
- [ ] Mark as "latest release"
- [ ] (Optional) Upload build artifacts

After release:
- [ ] Update CHANGELOG.md with release date
- [ ] Announce on social media (Twitter, LinkedIn)
- [ ] Submit to Hacker News (Show HN)
- [ ] Post on Reddit (r/cybersecurity, r/opensource)
- [ ] Monitor for issues/questions
- [ ] Respond to community feedback

---

**Ready to release?**

Run this from repository root:
```bash
./create_release.sh  # (if you create a script)
# OR manually:
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0 - Awakening 🧬" --notes-file RELEASE_v1.0.0.md --latest
```

Good luck with the launch! 🚀🧬
