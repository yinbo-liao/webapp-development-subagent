/**
 * Commit tokens: the bridge from an approved proposal to one execution.
 *
 * The token is an HMAC over (proposal id, args hash, intent hash, expiry). The
 * effect tool carries it; the pre-execute gate recomputes the binding from the
 * actual pending arguments, so a re-plan, a retry with different bytes, or a
 * redirect to another object cannot reuse an approval.
 */

import { createHmac, timingSafeEqual } from 'node:crypto'
import { ProposalError, type Proposal, type ProposalStore } from './proposals.js'

export type CommitErrorCode = 'invalid_token' | 'not_approved' | 'expired' | 'stale_args' | 'already_consumed'

/** Typed commit failure. */
export class CommitError extends Error {
  readonly code: CommitErrorCode

  constructor(code: CommitErrorCode, message: string) {
    super(message)
    this.name = 'CommitError'
    this.code = code
  }
}

/** The exact fields an approval authorises. */
export interface CommitBinding {
  readonly proposalId: string
  readonly argsHash: string
  readonly intentHash: string
  readonly expiresAt: number
}

function material(binding: CommitBinding): string {
  return `${binding.proposalId}|${binding.argsHash}|${binding.intentHash}|${binding.expiresAt}`
}

/** Mint a single-use commit token for an approved proposal. */
export function mintCommitToken(secret: string, binding: CommitBinding): string {
  return createHmac('sha256', secret).update(material(binding), 'utf8').digest('base64url')
}

/** Verify a token against a binding, in constant time. */
export function verifyCommitToken(secret: string, token: string, binding: CommitBinding): boolean {
  const expected = mintCommitToken(secret, binding)
  const left = Buffer.from(expected, 'utf8')
  const right = Buffer.from(token, 'utf8')
  if (left.length !== right.length) return false
  return timingSafeEqual(left, right)
}

export interface CommitInput {
  readonly proposalId: string
  readonly token: string
  /** Hash recomputed from the arguments of the call that is actually about to run. */
  readonly argsHash: string
  readonly secret: string
  readonly now?: number
}

/**
 * Verify the binding and consume the proposal exactly once.
 *
 * @throws {CommitError} on an invalid token, a stale hash, an expired approval,
 *   or a second commit.
 */
export function commitProposal(store: ProposalStore, input: CommitInput): Proposal {
  const proposal = store.get(input.proposalId)
  const now = input.now ?? Date.now()

  if (proposal.status === 'consumed' || proposal.status === 'verified') {
    throw new CommitError('already_consumed', `${proposal.id} was already executed`)
  }
  if (proposal.status === 'expired' || Date.parse(proposal.expiresAt) <= now) {
    throw new CommitError('expired', `${proposal.id} expired at ${proposal.expiresAt}`)
  }
  if (proposal.status !== 'approved') {
    throw new CommitError('not_approved', `${proposal.id} is ${proposal.status}`)
  }
  if (proposal.argsHash !== input.argsHash) {
    throw new CommitError('stale_args', 'arguments changed after approval')
  }

  const binding: CommitBinding = {
    proposalId: proposal.id,
    argsHash: proposal.argsHash,
    intentHash: proposal.intentHash,
    expiresAt: Date.parse(proposal.expiresAt),
  }
  if (!verifyCommitToken(input.secret, input.token, binding)) {
    throw new CommitError('invalid_token', 'commit token does not match this proposal')
  }

  try {
    return store.consume(proposal.id, { argsHash: input.argsHash, intentHash: proposal.intentHash })
  } catch (error) {
    if (error instanceof ProposalError && error.code === 'consumed') {
      throw new CommitError('already_consumed', error.message)
    }
    throw error
  }
}