#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'

export function pythonCommand() {
  const configured = process.env.OIP_PYTHON
  const candidates = configured
    ? [[configured, []]]
    : process.platform === 'win32'
      ? [['py', ['-3']], ['python', []], ['python3', []]]
      : [['python3', []], ['python', []]]

  for (const [command, prefix] of candidates) {
    const probe = spawnSync(command, [...prefix, '--version'], {
      encoding: 'utf8',
      windowsHide: true,
    })
    if (!probe.error && probe.status === 0) return { command, prefix }
  }
  throw new Error(
    'Python 3.10+ was not found. Install Python or set OIP_PYTHON to its executable.',
  )
}

export function spawnPython(args, options = {}) {
  const { command, prefix } = pythonCommand()
  return spawn(command, [...prefix, ...args], {
    windowsHide: true,
    ...options,
  })
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const child = spawnPython(process.argv.slice(2), { stdio: 'inherit' })
  child.on('error', (error) => {
    console.error(error.message)
    process.exitCode = 1
  })
  child.on('exit', (code, signal) => {
    process.exitCode = signal ? 1 : (code ?? 1)
  })
}
