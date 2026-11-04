#!/usr/bin/env node
/**
 * Zero-dependency validator for BusinessKPIContract.
 *
 * Usage:
 *   node contracts/validate-kpi.mjs contracts/example-kpi-contract.json
 *   node contracts/validate-kpi.mjs <file> --json
 *
 * Exit codes: 0 valid, 1 invalid, 2 usage/IO error.
 *
 * The schema file documents the shape; this validator adds the semantic rules a
 * JSON Schema cannot express: dates in the right order, a pre-registration before
 * the review, signatures from independent roles, and a guardrail for cost.
 */

import { readFile } from 'node:fs/promises'

const DATE = /^\d{4}-\d{2}-\d{2}$/
const DATE_TIME = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/
const ID = /^kpi-\d{4}-\d{3}$/
const FDE = /^fde:[a-z0-9._-]+$/
const SIGNER = /^(fde|product|security|engineering):[a-z0-9._-]+$/
const METRIC = /^[a-z][a-z0-9_]*$/
const WINDOW = /^\d{4}-\d{2}-\d{2}\/\d{4}-\d{2}-\d{2}$/

/** @param {unknown} value */
function isRecord(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** @param {string} date */
function day(date) {
  return Date.parse(`${date}T00:00:00Z`)
}

/**
 * @param {unknown} contract
 * @returns {{ errors: string[], warnings: string[] }}
 */
export function validateContract(contract) {
  /** @type {string[]} */
  const errors = []
  /** @type {string[]} */
  const warnings = []
  const fail = (message) => errors.push(message)
  const warn = (message) => warnings.push(message)

  if (!isRecord(contract)) return { errors: ['contract must be an object'], warnings }

  const required = [
    'contractId', 'feature', 'ownerFde', 'hypothesis', 'baseline', 'target',
    'guardrails', 'attribution', 'dataSources', 'decisionRule',
    'reviewDate', 'preRegisteredAt', 'signedBy',
  ]
  for (const key of required) {
    if (!(key in contract)) fail(`missing required field "${key}"`)
  }

  if (typeof contract.contractId !== 'string' || !ID.test(contract.contractId)) {
    fail('contractId must match kpi-YYYY-NNN')
  }
  if (typeof contract.feature !== 'string' || contract.feature.length < 3) fail('feature must be a non-empty string')
  if (typeof contract.ownerFde !== 'string' || !FDE.test(contract.ownerFde)) fail('ownerFde must match fde:<id>')
  if (typeof contract.hypothesis !== 'string' || contract.hypothesis.length < 20) {
    fail('hypothesis must be at least 20 characters and state the expected change')
  }

  if (!isRecord(contract.baseline)) {
    fail('baseline must be an object')
  } else {
    if (typeof contract.baseline.metric !== 'string' || !METRIC.test(contract.baseline.metric)) fail('baseline.metric must be snake_case')
    if (typeof contract.baseline.value !== 'number' || !Number.isFinite(contract.baseline.value)) fail('baseline.value must be a finite number')
    if (typeof contract.baseline.window !== 'string' || !WINDOW.test(contract.baseline.window)) fail('baseline.window must be YYYY-MM-DD/YYYY-MM-DD')
  }

  if (!isRecord(contract.target)) {
    fail('target must be an object')
  } else {
    if (typeof contract.target.metric !== 'string' || !METRIC.test(contract.target.metric)) fail('target.metric must be snake_case')
    if (typeof contract.target.value !== 'number' || !Number.isFinite(contract.target.value)) fail('target.value must be a finite number')
    if (typeof contract.target.byDate !== 'string' || !DATE.test(contract.target.byDate)) fail('target.byDate must be a date')
    if (isRecord(contract.baseline) && contract.baseline.metric !== contract.target.metric) {
      warn('baseline.metric and target.metric differ; state the conversion explicitly')
    }
  }

  if (!Array.isArray(contract.guardrails) || contract.guardrails.length === 0) {
    fail('guardrails must be a non-empty array')
  } else {
    for (const [index, guardrail] of contract.guardrails.entries()) {
      if (!isRecord(guardrail)) { fail(`guardrails[${index}] must be an object`); continue }
      if (typeof guardrail.metric !== 'string' || !METRIC.test(guardrail.metric)) fail(`guardrails[${index}].metric must be snake_case`)
      if (typeof guardrail.maxRegression !== 'number' || guardrail.maxRegression < 0) fail(`guardrails[${index}].maxRegression must be >= 0`)
    }
    if (!contract.guardrails.some((g) => isRecord(g) && g.metric === 'cost_per_success_usd')) {
      warn('no cost_per_success_usd guardrail: the contract does not cap the cost of moving the metric')
    }
  }

  if (!isRecord(contract.attribution)) {
    fail('attribution must be an object')
  } else if (!['pre_post', 'holdout', 'ab_test', 'interrupted_time_series'].includes(String(contract.attribution.method))) {
    fail('attribution.method must be one of pre_post, holdout, ab_test, interrupted_time_series')
  }

  if (!Array.isArray(contract.dataSources) || contract.dataSources.length === 0) {
    fail('dataSources must be a non-empty array')
  } else {
    for (const [index, source] of contract.dataSources.entries()) {
      if (!isRecord(source)) { fail(`dataSources[${index}] must be an object`); continue }
      for (const key of ['sourceId', 'system', 'queryRef', 'acl']) {
        if (typeof source[key] !== 'string' || source[key] === '') fail(`dataSources[${index}].${key} must be a non-empty string`)
      }
      if (source.aggregated !== true) fail(`dataSources[${index}].aggregated must be true (no row-level PII in the contract)`)
    }
  }

  if (!isRecord(contract.decisionRule)) {
    fail('decisionRule must be an object')
  } else {
    for (const key of ['continue', 'iterate', 'rollback']) {
      if (typeof contract.decisionRule[key] !== 'string' || contract.decisionRule[key].length < 10) {
        fail(`decisionRule.${key} must be a concrete rule (>= 10 chars)`)
      }
    }
  }

  if (typeof contract.reviewDate !== 'string' || !DATE.test(contract.reviewDate)) fail('reviewDate must be a date')
  if (typeof contract.preRegisteredAt !== 'string' || !DATE_TIME.test(contract.preRegisteredAt)) {
    fail('preRegisteredAt must be an ISO-8601 UTC date-time (e.g. 2026-11-10T09:00:00Z)')
  }

  if (Array.isArray(contract.signedBy)) {
    if (contract.signedBy.length < 2) fail('signedBy needs at least two signers')
    if (new Set(contract.signedBy).size !== contract.signedBy.length) fail('signedBy must not repeat a signer')
    for (const signer of contract.signedBy) {
      if (typeof signer !== 'string' || !SIGNER.test(signer)) fail(`invalid signer "${signer}" (expected fde:/product:/security:/engineering: prefix)`)
    }
    const hasFde = contract.signedBy.some((s) => typeof s === 'string' && s.startsWith('fde:'))
    const hasProduct = contract.signedBy.some((s) => typeof s === 'string' && s.startsWith('product:'))
    if (!hasFde || !hasProduct) fail('signedBy must include both the FDE and the product owner')
  } else {
    fail('signedBy must be an array')
  }

  if (typeof contract.preRegisteredAt === 'string' && DATE_TIME.test(contract.preRegisteredAt)) {
    const registered = Date.parse(contract.preRegisteredAt)
    if (typeof contract.reviewDate === 'string' && DATE.test(contract.reviewDate) && registered >= day(contract.reviewDate)) {
      fail('preRegisteredAt must be before reviewDate')
    }
    if (isRecord(contract.target) && typeof contract.target.byDate === 'string' && DATE.test(contract.target.byDate)
      && registered >= day(contract.target.byDate)) {
      fail('preRegisteredAt must be before target.byDate')
    }
  }
  if (typeof contract.reviewDate === 'string' && DATE.test(contract.reviewDate)
    && isRecord(contract.target) && typeof contract.target.byDate === 'string' && DATE.test(contract.target.byDate)
    && day(contract.reviewDate) < day(contract.target.byDate)) {
    fail('reviewDate must not precede target.byDate')
  }

  return { errors, warnings }
}

const isMain = process.argv[1] !== undefined && import.meta.url === new URL(`file://${process.argv[1].replace(/\\/g, '/')}`).href
if (isMain) {
  const file = process.argv[2]
  if (file === undefined) {
    console.error('usage: node contracts/validate-kpi.mjs <contract.json> [--json]')
    process.exit(2)
  }
  let parsed
  try {
    const text = (await readFile(file, 'utf8')).replace(/^\uFEFF/, '')
    parsed = JSON.parse(text)
  } catch (error) {
    console.error(`cannot read ${file}: ${error instanceof Error ? error.message : String(error)}`)
    process.exit(2)
  }
  const result = validateContract(parsed)
  if (process.argv.includes('--json')) {
    console.log(JSON.stringify(result, null, 2))
  } else {
    for (const warning of result.warnings) console.warn(`WARN  ${warning}`)
    for (const error of result.errors) console.error(`ERROR ${error}`)
    if (result.errors.length === 0) console.log(`OK    ${file}`)
  }
  process.exit(result.errors.length === 0 ? 0 : 1)
}
