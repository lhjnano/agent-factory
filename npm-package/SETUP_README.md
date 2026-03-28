# NPM Package Setup Complete

This directory contains the npm wrapper package for Agent Factory.

## Files

- `package.json` - NPM package configuration
- `index.js` - Node.js wrapper script that launches Python MCP server
- `README.md` - Package documentation for npm users
- `PUBLISHING.md` - Guide for publishing to npm registry
- `test.sh` - Test script for the wrapper

## Installation

### Local Testing

To test this package locally:

```bash
cd npm-package
npm link
```

Then test:

```bash
npx -y @purpleraven/agent-factory
```

### Publishing to npm

See `PUBLISHING.md` for detailed instructions:

```bash
cd npm-package
npm publish --access public
```

## Features of the Wrapper

The `index.js` wrapper provides:

1. **Auto-detection of Agent Factory installation**
   - Checks `AGENT_FACTORY_PATH` environment variable
   - Searches common directories: `~/source/agent-factory`, `~/agent-factory`, etc.
   - Works with cloned repositories or installed packages

2. **Automatic virtual environment detection**
   - Checks `AGENT_FACTORY_VENV` environment variable
   - Looks for venv in standard locations
   - Falls back to system Python 3

3. **Error handling**
   - Clear error messages if Agent Factory not found
   - Lists all searched directories
   - Provides setup instructions

4. **Signal handling**
   - Properly forwards SIGINT and SIGTERM to Python process
   - Clean shutdown on exit

## Usage in OpenCode

After publishing to npm, users can use:

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

## Environment Variables

Users can customize with:

- `AGENT_FACTORY_PATH` - Override auto-detection with specific path
- `AGENT_FACTORY_VENV` - Use specific virtual environment

## Next Steps

1. **Test locally**: Run `./test.sh` to verify everything works
2. **Publish**: Follow `PUBLISHING.md` to publish to npm
3. **Update documentation**: Mention npm option in main docs
4. **Verify**: Test with OpenCode after publishing

---

**Status:** Ready for publishing
**Package Name:** @purpleraven/agent-factory
**Version:** 2.1.0
