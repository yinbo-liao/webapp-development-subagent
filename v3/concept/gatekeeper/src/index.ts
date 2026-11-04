/**
 * Gatekeeper core (P1 slice): policy decisions, proposal state machine, commit
 * tokens. The DSH plugin wires these to tools/pre-execute, ctx.tools.guard and
 * ctx.approval; this package has no DSH dependency so it can be tested alone.
 */

import { readFileSync } from 'node:fs'
import type { EffectMatrix } from './types.js'

export type * from './types.js'
export { autonomyFor, decide, findModelOverride, requiredGuardrails } from './policy.js'
export {
  ProposalError, ProposalStore, argsHash, canonicalJson, intentHash,
} from './proposals.js'
export type {
  CreateProposalInput, Proposal, ProposalErrorCode, ProposalStatus, ProposalStoreOptions,
} from './proposals.js'
export {
  CommitError, commitProposal, mintCommitToken, verifyCommitToken,
} from './commit.js'
export type { CommitBinding, CommitErrorCode, CommitInput } from './commit.js'

/** Load an effect matrix from JSON (generated from `policy/effect-matrix.yaml`). */
export function loadMatrix(path: string): EffectMatrix {
  return JSON.parse(readFileSync(path, 'utf8')) as EffectMatrix
}