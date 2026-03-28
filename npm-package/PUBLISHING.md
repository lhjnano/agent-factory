# Publishing @purpleraven/agent-factory to NPM

This guide explains how to publish the Agent Factory npm wrapper package to npm registry.

## Prerequisites

1. **npm account**: You need an npm account at https://www.npmjs.com
2. **npm login**: Authenticate with npm
3. **npm scope**: `@purpleraven` scope must be configured

## Setup

### 1. Login to npm

```bash
npm login
```

Enter your npm username, password, and email when prompted.

### 2. Verify npm scope

The package uses the `@purpleraven` scope. Ensure you have access to this scope:

```bash
npm profile get
```

You should see `@purpleraven` in your packages or scope settings.

## Publishing

### Step 1: Update Version (if needed)

Edit `package.json` and update the version number:

```json
{
  "name": "@purpleraven/agent-factory",
  "version": "2.1.0"
}
```

Or use npm version command:

```bash
cd npm-package
npm version patch      # 2.1.0 -> 2.1.1
npm version minor      # 2.1.0 -> 2.2.0
npm version major      # 2.1.0 -> 3.0.0
```

### Step 2: Test Locally

Before publishing, test the package locally:

```bash
cd npm-package
npm link
```

Then test it:

```bash
npx -y @purpleraven/agent-factory
```

Or use it in another project:

```bash
npm link @purpleraven/agent-factory
```

### Step 3: Run Tests

```bash
cd npm-package
chmod +x test.sh
./test.sh
```

### Step 4. Publish to npm

```bash
cd npm-package
npm publish --access public
```

**Note:** The `--access public` flag is required for scoped packages.

### Step 5: Verify

Verify the package is published:

```bash
npm view @purpleraven/agent-factory
```

Or visit: https://www.npmjs.com/package/@purpleraven/agent-factory

## Post-Publishing

### Update OpenCode Documentation

After publishing, update the documentation to reference the npm package:

1. Update `docs/OPENCODE_USAGE_GUIDE.md` to mention npx usage
2. Update `docs/SETUP.md` with npm installation instructions
3. Update `INSTALLATION_COMPLETE.md` with npx examples

### Test with OpenCode

Update your `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "agent-factory": {
      "type": "local",
      "command": [
        "npx",
        "-y",
        "@purpleraven/agent-factory"
      ]
    }
  }
}
```

Then restart OpenCode and verify the MCP tools appear.

## Version Management

Follow semantic versioning:

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Example: `2.1.0` (MAJOR.MINOR.PATCH)

## Troubleshooting

### Error: "403 Forbidden"

This means you don't have permission to publish to the `@purpleraven` scope.

**Solution:**
1. Verify you're logged in to the correct npm account
2. Ensure the `@purpleraven` scope is linked to your account
3. Contact scope owner if you're not the owner

### Error: "Package name already exists"

The package name `@purpleraven/agent-factory` is already published.

**Solution:**
- Update version number and republish
- Or use `npm publish --force` (not recommended for production)

### Error: "404 Not Found" on install

This usually means the package was not published or has an invalid name.

**Solution:**
1. Check if package exists: `npm view @purpleraven/agent-factory`
2. Verify package.json name matches exactly
3. Ensure you used `--access public` flag

## Continuous Updates

When you update the Agent Factory Python code, you may need to update the npm wrapper if:

1. New environment variables are required
2. New Python path detection logic is needed
3. Configuration options change

The npm wrapper version should be kept in sync with the Python package version.

## Unpublishing (Emergency Only)

If you need to remove a published version:

```bash
npm unpublish @purpleraven/agent-factory@version
```

**Warning:** You can only unpublish versions published within the last 72 hours.

---

**Last Updated:** 2026-03-28
