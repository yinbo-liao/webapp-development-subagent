/**
 * Commit tokens: the bridge from an approved proposal to one execution.
 *
 * The token is an HMAC over (proposal id, args hash, intent hash, expiry). The
 * effect tool carries it; the pre-execute gate recomputes the binding from the
 * actual pending arguments, so a re-plan, a retry with different bytes, or a
 * redirect to another object cannot reuse an approval.
 */
import { type Proposal, type ProposalStore } from './proposals.js';
export type CommitErrorCode = 'invalid_token' | 'not_approved' | 'expired' | 'stale_args' | 'already_consumed';
/** Typed commit failure. */
export declare class CommitError extends Error {
    readonly code: CommitErrorCode;
    constructor(code: CommitErrorCode, message: string);
}
/** The exact fields an approval authorises. */
export interface CommitBinding {
    readonly proposalId: string;
    readonly argsHash: string;
    readonly intentHash: string;
    readonly expiresAt: number;
}
/** Mint a single-use commit token for an approved proposal. */
export declare function mintCommitToken(secret: string, binding: CommitBinding): string;
/** Verify a token against a binding, in constant time. */
export declare function verifyCommitToken(secret: string, token: string, binding: CommitBinding): boolean;
export interface CommitInput {
    readonly proposalId: string;
    readonly token: string;
    /** Hash recomputed from the arguments of the call that is actually about to run. */
    readonly argsHash: string;
    readonly secret: string;
    readonly now?: number;
}
/**
 * Verify the binding and consume the proposal exactly once.
 *
 * @throws {CommitError} on an invalid token, a stale hash, an expired approval,
 *   or a second commit.
 */
export declare function commitProposal(store: ProposalStore, input: CommitInput): Proposal;
