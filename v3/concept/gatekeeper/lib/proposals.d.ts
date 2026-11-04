/**
 * Proposals: approval bound to the exact bytes.
 *
 * A human approves a proposal, not a task. The proposal carries the canonical
 * hash of (tool, args) and the intent hash; execution is allowed once, for those
 * bytes, within the TTL. This is the TypeScript port of
 * `reference/agentkit/proposals.py`, and the Python module remains the oracle.
 */
export type ProposalStatus = 'pending' | 'approved' | 'rejected' | 'expired' | 'consumed' | 'verified';
export interface Proposal {
    readonly id: string;
    readonly runId: string;
    readonly dispatchId: string;
    readonly role: string;
    readonly tool: string;
    readonly effect: string;
    readonly args: Readonly<Record<string, unknown>>;
    readonly argsHash: string;
    readonly intentHash: string;
    readonly blastRadius: string;
    readonly rollbackPlan: string;
    readonly verificationPlan: string;
    readonly idempotencyKey: string;
    readonly createdAt: string;
    readonly expiresAt: string;
    status: ProposalStatus;
    decidedBy?: string;
    decidedAt?: string;
    checklistHash?: string;
    note?: string;
    verifiedBy?: string;
    verifiedAt?: string;
}
export type ProposalErrorCode = 'not_found' | 'already_decided' | 'expired' | 'consumed' | 'stale_args' | 'not_approved' | 'rejected' | 'intent_mismatch' | 'invalid_checklist';
/** Typed proposal failure; the gatekeeper maps codes to model-facing denials. */
export declare class ProposalError extends Error {
    readonly code: ProposalErrorCode;
    readonly proposalId: string | undefined;
    constructor(code: ProposalErrorCode, message: string, proposalId?: string);
}
/** Canonical JSON: object keys sorted so hashes do not depend on insertion order. */
export declare function canonicalJson(value: unknown): string;
/** Canonical hash of (tool, args); the one identifier the store and the gate share. */
export declare function argsHash(tool: string, args: Readonly<Record<string, unknown>>): string;
/** Stable hash of the user's stated scope; two runs of the same request agree. */
export declare function intentHash(intent: Readonly<Record<string, unknown>> | undefined): string;
export interface CreateProposalInput {
    readonly runId: string;
    readonly dispatchId?: string;
    readonly role: string;
    readonly tool: string;
    readonly effect: string;
    readonly args: Readonly<Record<string, unknown>>;
    readonly intent?: Readonly<Record<string, unknown>>;
    readonly blastRadius: string;
    readonly rollbackPlan: string;
    readonly verificationPlan: string;
    readonly ttlMs?: number;
}
export interface ProposalStoreOptions {
    readonly ttlMs?: number;
    /** Injectable clock (epoch ms) for deterministic tests. */
    readonly now?: () => number;
}
/** In-memory proposal store; the plugin swaps the persistence layer, not the state machine. */
export declare class ProposalStore {
    #private;
    constructor(options?: ProposalStoreOptions);
    /** Create a proposal, reusing a live one for the same run/tool/args. */
    create(input: CreateProposalInput): Proposal;
    /** Look up a proposal or throw `not_found`. */
    get(proposalId: string): Proposal;
    /** Approve a pending proposal; the args hash must still match what was reviewed. */
    approve(proposalId: string, input: {
        by: string;
        argsHash: string;
        checklistHash: string;
        note?: string;
    }): Proposal;
    /** Reject a pending proposal. */
    reject(proposalId: string, input: {
        by: string;
        note?: string;
    }): Proposal;
    /** Consume an approved proposal exactly once, for the approved bytes and intent. */
    consume(proposalId: string, input: {
        argsHash: string;
        intentHash?: string;
    }): Proposal;
    /** Mark a consumed proposal as verified by reading back the side effect. */
    verify(proposalId: string, input: {
        by: string;
    }): Proposal;
    /** Expire every live proposal past its TTL. */
    expire(): number;
    /** Pending proposals, optionally for one run. */
    pending(runId?: string): Proposal[];
    /** Counts by status. */
    stats(): Record<string, number>;
}
