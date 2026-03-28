#!/usr/bin/env node

/**
 * Agent Factory MCP Server - NPM Wrapper
 *
 * This wrapper launches the Python MCP server for Agent Factory.
 * It detects the Agent Factory installation location from environment variables
 * or searches common installation directories.
 *
 * Usage:
 *   npx -y @purpleraven/agent-factory
 *
 * Environment Variables:
 *   AGENT_FACTORY_PATH - Path to agent-factory installation (optional)
 *   AGENT_FACTORY_VENV - Path to virtual environment (optional)
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

/**
 * Find Agent Factory installation directory
 */
function findAgentFactoryPath() {
  // 1. Check environment variable
  if (process.env.AGENT_FACTORY_PATH) {
    const resolvedPath = path.resolve(process.env.AGENT_FACTORY_PATH);
    if (fs.existsSync(resolvedPath)) {
      console.error(`[Agent Factory] Using path from AGENT_FACTORY_PATH: ${resolvedPath}`);
      return resolvedPath;
    }
  }

  // 2. Check common installation directories
  const homeDir = os.homedir();
  const commonPaths = [
    path.join(homeDir, 'source', 'agent-factory'),
    path.join(homeDir, 'agent-factory'),
    path.join(homeDir, 'projects', 'agent-factory'),
    path.join(process.cwd(), 'agent-factory'),
    path.join(process.cwd(), '..'), // If running from subdirectory
    path.join(__dirname, '..'), // If npm package is inside agent-factory
  ];

  for (const dir of commonPaths) {
    const resolvedPath = path.resolve(dir);
    if (fs.existsSync(path.join(resolvedPath, 'src', 'agent_factory'))) {
      console.error(`[Agent Factory] Found installation at: ${resolvedPath}`);
      return resolvedPath;
    }
  }

  // 3. Not found - error
  console.error(`[Agent Factory] ERROR: Agent Factory installation not found!`);
  console.error(`[Agent Factory] Tried the following paths:`);
  commonPaths.forEach(p => console.error(`[Agent Factory]   - ${p}`));
  console.error(`[Agent Factory]`);
  console.error(`[Agent Factory] Please set AGENT_FACTORY_PATH environment variable:`);
  console.error(`[Agent Factory]   export AGENT_FACTORY_PATH=/path/to/agent-factory`);
  process.exit(1);
}

/**
 * Get Python interpreter path
 */
function getPythonPath(agentFactoryPath) {
  // 1. Check environment variable
  if (process.env.AGENT_FACTORY_VENV) {
    const venvPath = path.resolve(process.env.AGENT_FACTORY_VENV, 'bin', 'python');
    if (fs.existsSync(venvPath)) {
      console.error(`[Agent Factory] Using venv from AGENT_FACTORY_VENV: ${venvPath}`);
      return venvPath;
    }
  }

  // 2. Check for venv in agent-factory directory
  const venvPaths = [
    path.join(agentFactoryPath, 'venv', 'bin', 'python'),
    path.join(agentFactoryPath, '.venv', 'bin', 'python'),
  ];

  for (const venvPath of venvPaths) {
    if (fs.existsSync(venvPath)) {
      console.error(`[Agent Factory] Using venv: ${venvPath}`);
      return venvPath;
    }
  }

  // 3. Use system python3
  console.error(`[Agent Factory] Using system python3`);
  return 'python3';
}

/**
 * Main function
 */
function main() {
  const agentFactoryPath = findAgentFactoryPath();
  const pythonPath = getPythonPath(agentFactoryPath);

  console.error(`[Agent Factory] Starting MCP server...`);
  console.error(`[Agent Factory]   Agent Factory: ${agentFactoryPath}`);
  console.error(`[Agent Factory]   Python: ${pythonPath}`);
  console.error(`[Agent Factory]`);

  // Launch Python MCP server
  const pythonProcess = spawn(
    pythonPath,
    ['-m', 'agent_factory.mcp_server'],
    {
      cwd: agentFactoryPath,
      env: {
        ...process.env,
        AGENT_FACTORY_PATH: agentFactoryPath,
        PYTHONPATH: path.join(agentFactoryPath, 'src'),
      },
      stdio: 'inherit' // Connect stdin/stdout/stderr to parent process
    }
  );

  // Handle process exit
  pythonProcess.on('error', (error) => {
    console.error(`[Agent Factory] ERROR: Failed to start Python process: ${error.message}`);
    process.exit(1);
  });

  pythonProcess.on('exit', (code, signal) => {
    if (signal) {
      console.error(`[Agent Factory] Terminated by signal: ${signal}`);
    } else {
      console.error(`[Agent Factory] Exited with code: ${code}`);
    }
    process.exit(code || 0);
  });

  // Forward exit signals
  process.on('SIGINT', () => {
    console.error(`[Agent Factory] Received SIGINT, shutting down...`);
    pythonProcess.kill('SIGINT');
  });

  process.on('SIGTERM', () => {
    console.error(`[Agent Factory] Received SIGTERM, shutting down...`);
    pythonProcess.kill('SIGTERM');
  });
}

// Run main function
main();
