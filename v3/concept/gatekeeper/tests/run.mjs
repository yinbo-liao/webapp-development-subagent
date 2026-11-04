import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import {
  CommitError, ProposalError, ProposalStore, commitProposal, decide, findModelOverride,
  loadMatrix, mintCommitToken,
} from '../lib/index.js'

let passed = 0
let failed = 0
function test(name, fn) {
  try {
    fn()
    passed += 1
    console.log(`ok   ${name}`)
  } catch (error) {
    failed += 1
    console.error(`FAIL ${name}\n     ${error instanceof Error ? error.message : String(error)}`)
  }
}

const matrix = loadMatrix(fileURLToPath(new URL('../../policy/effect-matrix.json', import.meta.url)))
const builderSchemaGuardrails = matrix.guardrails.builder.change_schema

test('builder writes a migration inside guardrails', () => {
  const outcome = decide(matrix, 'builder', 'change_schema', { guardrailsSatisfied: builderSchemaGuardrails })
  assert.equal(outcome.kind, 'allow')
  assert.equal(outcome.mode, 'auto')
})

test('builder without guardrail evidence fails closed', () => {
  const outcome = decide(matrix, 'builder', 'change_schema', { guardrailsSatisfied: [] })
  assert.equal(outcome.kind, 'deny')
  assert.equal(outcome.code, 'GUARDRAIL_UNVERIFIED')
})

test('builder cannot deploy production', () => {
  const outcome = decide(matrix, 'builder', 'deploy_prod')
  assert.equal(outcome.kind, 'deny')
  assert.equal(outcome.code, 'POLICY_FORBIDDEN')
})

test('operator deploy is an approval, not an autonomy', () => {
  const outcome = decide(matrix, 'operator', 'deploy_prod')
  assert.equal(outcome.kind, 'ask')
})

test('kill switch freezes effects but not reads', () => {
  assert.equal(decide(matrix, 'operator', 'deploy_prod', { killSwitch: true }).code, 'KILL_SWITCH')
  assert.equal(decide(matrix, 'analyst', 'read_repo', { killSwitch: true }).kind, 'allow')
})

test('unknown effects and roles fail closed', () => {
  assert.equal(decide(matrix, 'builder', 'delete_everything').code, 'UNKNOWN_EFFECT')
  assert.equal(decide(matrix, 'intruder', 'read_repo').code, 'UNKNOWN_ROLE')
})

test('human wildcard allows without guardrails', () => {
  assert.equal(decide(matrix, 'human', 'deploy_prod').kind, 'allow')
})

test('model overrides are detected at any depth', () => {
  assert.equal(findModelOverride({ url: 'https://x', options: { model: 'x' } }), 'options.model')
  assert.equal(findModelOverride({ provider: 'x' }), 'provider')
  assert.equal(findModelOverride({ url: 'https://x' }), undefined)
})

let clock = Date.parse('2026-11-04T00:00:00Z')
const now = () => clock
const store = new ProposalStore({ ttlMs: 60_000, now })

function makeProposal() {
  return store.create({
    runId: 'run-1',
    role: 'operator',
    tool: 'deploy_prod',
    effect: 'deploy_prod',
    args: { service: 'api', image: 'sha256:abc' },
    intent: { feature: 'P-01', cohort: 'internal' },
    blastRadius: 'internal cohort only',
    rollbackPlan: 'revert image to previous digest',
    verificationPlan: 'smoke + error-rate check',
  })
}

test('proposal creation is idempotent while pending', () => {
  const first = makeProposal()
  const second = makeProposal()
  assert.equal(first.id, second.id)
  assert.equal(first.status, 'pending')
})

test('approval binds to the args hash', () => {
  const proposal = makeProposal()
  assert.throws(() => store.approve(proposal.id, { by: 'fde:jdoe', argsHash: 'deadbeef', checklistHash: 'a'.repeat(16) }), (error) => error instanceof ProposalError && error.code === 'stale_args')
  const approved = store.approve(proposal.id, { by: 'fde:jdoe', argsHash: proposal.argsHash, checklistHash: 'a'.repeat(16) })
  assert.equal(approved.status, 'approved')
})

test('approval requires a checklist acknowledgement', () => {
  const proposal = makeProposal()
  assert.throws(() => store.approve(proposal.id, { by: 'fde:jdoe', argsHash: proposal.argsHash, checklistHash: '' }), (error) => error instanceof ProposalError && error.code === 'invalid_checklist')
})

test('consume is single-use and intent-bound', () => {
  const proposal = makeProposal()
  store.approve(proposal.id, { by: 'fde:jdoe', argsHash: proposal.argsHash, checklistHash: 'b'.repeat(16) })
  assert.throws(() => store.consume(proposal.id, { argsHash: proposal.argsHash, intentHash: 'other' }), (error) => error instanceof ProposalError && error.code === 'intent_mismatch')
  const consumed = store.consume(proposal.id, { argsHash: proposal.argsHash, intentHash: proposal.intentHash })
  assert.equal(consumed.status, 'consumed')
  assert.throws(() => store.consume(proposal.id, { argsHash: proposal.argsHash }), (error) => error instanceof ProposalError && error.code === 'consumed')
  const verified = store.verify(proposal.id, { by: 'operator' })
  assert.equal(verified.status, 'verified')
})

test('proposals expire on the injected clock', () => {
  const proposal = store.create({
    runId: 'run-2', role: 'operator', tool: 'deploy_prod', effect: 'deploy_prod', args: { n: 1 },
    blastRadius: 'x', rollbackPlan: 'y', verificationPlan: 'z',
  })
  clock += 120_000
  assert.throws(() => store.approve(proposal.id, { by: 'fde:jdoe', argsHash: proposal.argsHash, checklistHash: 'c'.repeat(16) }), (error) => error instanceof ProposalError && error.code === 'expired')
  clock = Date.parse('2026-11-04T00:00:00Z')
})

test('rejected proposals cannot be approved later', () => {
  const proposal = store.create({
    runId: 'run-3', role: 'operator', tool: 'deploy_prod', effect: 'deploy_prod', args: { n: 2 },
    blastRadius: 'x', rollbackPlan: 'y', verificationPlan: 'z',
  })
  store.reject(proposal.id, { by: 'fde:jdoe', note: 'not this week' })
  assert.throws(() => store.approve(proposal.id, { by: 'fde:jdoe', argsHash: proposal.argsHash, checklistHash: 'd'.repeat(16) }), (error) => error instanceof ProposalError && error.code === 'already_decided')
})

test('commit token binds proposal, args, intent and expiry', () => {
  const secret = 'test-secret'
  const proposal = store.create({
    runId: 'run-4', role: 'operator', tool: 'deploy_prod', effect: 'deploy_prod', args: { n: 3 },
    blastRadius: 'x', rollbackPlan: 'y', verificationPlan: 'z',
  })
  store.approve(proposal.id, { by: 'fde:jdoe', argsHash: proposal.argsHash, checklistHash: 'e'.repeat(16) })
  const binding = { proposalId: proposal.id, argsHash: proposal.argsHash, intentHash: proposal.intentHash, expiresAt: Date.parse(proposal.expiresAt) }
  const token = mintCommitToken(secret, binding)

  assert.throws(() => commitProposal(store, { proposalId: proposal.id, token, argsHash: 'changed', secret, now: clock }), (error) => error instanceof CommitError && error.code === 'stale_args')
  assert.throws(() => commitProposal(store, { proposalId: proposal.id, token: `${token}x`, argsHash: proposal.argsHash, secret, now: clock }), (error) => error instanceof CommitError && error.code === 'invalid_token')

  const consumed = commitProposal(store, { proposalId: proposal.id, token, argsHash: proposal.argsHash, secret, now: clock })
  assert.equal(consumed.status, 'consumed')
  assert.throws(() => commitProposal(store, { proposalId: proposal.id, token, argsHash: proposal.argsHash, secret, now: clock }), (error) => error instanceof CommitError && error.code === 'already_consumed')
})

console.log(`\n${passed} passed, ${failed} failed`)
process.exit(failed === 0 ? 0 : 1)