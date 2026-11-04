#!/usr/bin/env node
/**
 * Document-integrity check for design documents.
 *
 * Why this exists: the v3.0 design arrived with a single unclosed code fence at
 * §2.1, which makes every later section render as code, and with plain-text
 * "headings" that break navigation. A document that claims "implementation-ready"
 * should pass the same kind of check as code.
 *
 * Checks:
 *   1. Code fences are balanced; an unclosed fence is reported with its line.
 *   2. Numbered section lines (e.g. "3.2 analyst") are real Markdown headings.
 *   3. No model meta-commentary in the deliverable ("That is the full markdown file").
 *   4. Version/status fields exist; an "implementation-ready" claim requires a
 *      test/acceptance section to exist.
 *   5. Required section titles (optional --require) are present as headings.
 *
 * Usage:
 *   node tools/check-doc.mjs <file.md> [--json] [--require "0.,1.,2.,11.,16."]
 *
 * Exit codes: 0 pass (warnings allowed), 1 fail, 2 usage/IO error.
 */

import { readFile } from 'node:fs/promises'

const args = process.argv.slice(2)
const file = args.find((arg) => !arg.startsWith('--'))
const asJson = args.includes('--json')
const requireIndex = args.indexOf('--require')
const required = requireIndex >= 0 ? (args[requireIndex + 1] ?? '').split(',').map((s) => s.trim()).filter(Boolean) : []

if (file === undefined) {
  console.error('usage: node tools/check-doc.mjs <file.md> [--json] [--require "0.,1.,2."]')
  process.exit(2)
}

let text
try {
  text = (await readFile(file, 'utf8')).replace(/^\uFEFF/, '')
} catch (error) {
  console.error(`cannot read ${file}: ${error instanceof Error ? error.message : String(error)}`)
  process.exit(2)
}

const lines = text.split(/\r?\n/)
const errors = []
const warnings = []

// 1. Fences
const fences = []
for (let i = 0; i < lines.length; i += 1) {
  if (/^\s*```/.test(lines[i])) fences.push({ line: i + 1, text: lines[i].trim() })
}
const fencesBalanced = fences.length % 2 === 0
if (!fencesBalanced) {
  errors.push(`unclosed code fence: opened at line ${fences[fences.length - 1].line} ("${fences[fences.length - 1].text}") and never closed`)
}

// 2. Headings and plain-text sections
const headings = []
for (let i = 0; i < lines.length; i += 1) {
  if (/^#{1,6}\s/.test(lines[i])) headings.push({ line: i + 1, level: (lines[i].match(/^#+/) ?? [''])[0].length, text: lines[i] })
}
const plainSections = []
for (let i = 0; i < lines.length; i += 1) {
  const line = lines[i]
  if (/^\d+(\.\d+)?\s+[A-Z]/.test(line) && !/^#{1,6}\s/.test(line)) {
    plainSections.push({ line: i + 1, text: line.slice(0, 80) })
  }
}
if (plainSections.length > 0) {
  errors.push(`${plainSections.length} numbered section line(s) are not Markdown headings (first: line ${plainSections[0].line} "${plainSections[0].text}")`)
}

// 3. Meta commentary
const metaPattern = /That is the full markdown file|It integrates:|This is the full markdown/i
for (let i = 0; i < lines.length; i += 1) {
  if (metaPattern.test(lines[i])) errors.push(`model meta-commentary in the deliverable at line ${i + 1}`)
}

// 4. Version / status
const versionLine = lines.find((line) => /^\*\*Version:\*\*/i.test(line.trim()))
const statusLine = lines.find((line) => /^\*\*Status:\*\*/i.test(line.trim()))
if (versionLine === undefined) warnings.push('no **Version:** field')
if (statusLine === undefined) warnings.push('no **Status:** field')
const claimsReady = statusLine !== undefined && /implementation-ready/i.test(statusLine)
if (claimsReady) {
  const hasTestSection = headings.some((h) => /test|verification|acceptance/i.test(h.text))
  if (!hasTestSection) errors.push('status claims "implementation-ready" but no test/verification/acceptance heading exists')
}

// 5. Required sections
for (const token of required) {
  const present = headings.some((h) => h.text.replace(/^#+\s*/, '').startsWith(token))
  if (!present) errors.push(`required section "${token}" is missing or not a heading`)
}

const level2 = headings.filter((h) => h.level === 2).length
const summary = {
  file,
  lines: lines.length,
  fences: { count: fences.length, balanced: fencesBalanced },
  headings: { total: headings.length, level2 },
  plainTextSections: plainSections.length,
  metaCommentary: lines.filter((line) => metaPattern.test(line)).length,
  version: versionLine?.trim() ?? null,
  status: statusLine?.trim() ?? null,
  errors,
  warnings,
  pass: errors.length === 0,
}

if (asJson) {
  console.log(JSON.stringify(summary, null, 2))
} else {
  console.log(`file:   ${file}`)
  console.log(`lines:  ${summary.lines}`)
  console.log(`fences: ${summary.fences.count} (${summary.fences.balanced ? 'balanced' : 'UNBALANCED'})`)
  console.log(`headings: ${summary.headings.total} (level 2: ${level2})`)
  console.log(`plain-text sections: ${summary.plainTextSections}`)
  for (const warning of warnings) console.warn(`WARN  ${warning}`)
  for (const error of errors) console.error(`ERROR ${error}`)
  console.log(summary.pass ? 'PASS' : `FAIL (${errors.length} error${errors.length === 1 ? '' : 's'})`)
}
process.exit(summary.pass ? 0 : 1)