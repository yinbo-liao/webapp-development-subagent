/**
 * Proposals: approval bound to the exact bytes.
 *
 * A human approves a proposal, not a task. The proposal carries the canonical
 * hash of (tool, args) and the intent hash; execution is allowed once, for those
 * bytes, within the TTL. This is the TypeScript port of
 * `reference/agentkit/proposals.py`, and the Python module remains the oracle.
 */
import { createHash } from 'node:crypto';
/** Typed proposal failure; the gatekeeper maps codes to model-facing denials. */
export class ProposalError extends Error {
    code;
    proposalId;
    constructor(code, message, proposalId) {
        super(message);
        this.name = 'ProposalError';
        this.code = code;
        this.proposalId = proposalId;
    }
}
/** Canonical JSON: object keys sorted so hashes do not depend on insertion order. */
export function canonicalJson(value) {
    if (value === null || typeof value !== 'object')
        return JSON.stringify(value) ?? 'null';
    if (Array.isArray(value))
        return `[${value.map(canonicalJson).join(',')}]`;
    const entries = Object.entries(value)
        .filter(([, entry]) => entry !== undefined)
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    return `{${entries.map(([key, entry]) => `${JSON.stringify(key)}:${canonicalJson(entry)}`).join(',')}}`;
}
function sha256(value) {
    return createHash('sha256').update(value, 'utf8').digest('hex');
}
/** Canonical hash of (tool, args); the one identifier the store and the gate share. */
export function argsHash(tool, args) {
    return sha256(canonicalJson({ tool, args })).slice(0, 32);
}
/** Stable hash of the user's stated scope; two runs of the same request agree. */
export function intentHash(intent) {
    return sha256(canonicalJson({ intent: intent ?? {} })).slice(0, 32);
}
const DEFAULT_TTL_MS = 60 * 60 * 1000;
/** In-memory proposal store; the plugin swaps the persistence layer, not the state machine. */
export class ProposalStore {
    #ttlMs;
    #now;
    #byId = new Map();
    constructor(options = {}) {
        this.#ttlMs = options.ttlMs ?? DEFAULT_TTL_MS;
        this.#now = options.now ?? (() => Date.now());
    }
    /** Create a proposal, reusing a live one for the same run/tool/args. */
    create(input) {
        const hash = argsHash(input.tool, input.args);
        const intent = intentHash(input.intent);
        for (const existing of this.#byId.values()) {
            if (existing.runId === input.runId && existing.tool === input.tool
                && existing.argsHash === hash && existing.status === 'pending') {
                return existing;
            }
        }
        const now = this.#now();
        const base = `prop_${sha256(`${input.runId}|${input.tool}|${hash}|${intent}`).slice(0, 12)}`;
        let id = base;
        let suffix = 2;
        while (this.#byId.has(id)) {
            id = `${base}-${suffix}`;
            suffix += 1;
        }
        const ttl = input.ttlMs ?? this.#ttlMs;
        const proposal = {
            id,
            runId: input.runId,
            dispatchId: input.dispatchId ?? '',
            role: input.role,
            tool: input.tool,
            effect: input.effect,
            args: input.args,
            argsHash: hash,
            intentHash: intent,
            blastRadius: input.blastRadius,
            rollbackPlan: input.rollbackPlan,
            verificationPlan: input.verificationPlan,
            idempotencyKey: sha256(`${input.runId}|${input.tool}|${hash}`).slice(0, 32),
            createdAt: new Date(now).toISOString(),
            expiresAt: new Date(now + ttl).toISOString(),
            status: 'pending',
        };
        this.#byId.set(id, proposal);
        return proposal;
    }
    /** Look up a proposal or throw `not_found`. */
    get(proposalId) {
        const proposal = this.#byId.get(proposalId);
        if (proposal === undefined)
            throw new ProposalError('not_found', `unknown proposal ${proposalId}`, proposalId);
        return proposal;
    }
    #assertLive(proposal) {
        if (proposal.status === 'expired' || Date.parse(proposal.expiresAt) <= this.#now()) {
            if (proposal.status === 'pending' || proposal.status === 'approved')
                proposal.status = 'expired';
            throw new ProposalError('expired', `${proposal.id} expired at ${proposal.expiresAt}`, proposal.id);
        }
    }
    /** Approve a pending proposal; the args hash must still match what was reviewed. */
    approve(proposalId, input) {
        const proposal = this.get(proposalId);
        this.#assertLive(proposal);
        if (proposal.status === 'consumed')
            throw new ProposalError('consumed', `${proposalId} was executed`, proposalId);
        if (proposal.status === 'verified')
            throw new ProposalError('already_decided', `${proposalId} is verified`, proposalId);
        if (proposal.status !== 'pending')
            throw new ProposalError('already_decided', `${proposalId} is ${proposal.status}`, proposalId);
        if (input.argsHash !== proposal.argsHash) {
            throw new ProposalError('stale_args', `args changed after review for ${proposalId}`, proposalId);
        }
        if (!/^[0-9a-f]{16,}$/.test(input.checklistHash)) {
            throw new ProposalError('invalid_checklist', 'approval requires a checklist acknowledgement hash', proposalId);
        }
        proposal.status = 'approved';
        proposal.decidedBy = input.by;
        proposal.decidedAt = new Date(this.#now()).toISOString();
        proposal.checklistHash = input.checklistHash;
        if (input.note !== undefined)
            proposal.note = input.note;
        return proposal;
    }
    /** Reject a pending proposal. */
    reject(proposalId, input) {
        const proposal = this.get(proposalId);
        if (proposal.status !== 'pending')
            throw new ProposalError('already_decided', `${proposalId} is ${proposal.status}`, proposalId);
        proposal.status = 'rejected';
        proposal.decidedBy = input.by;
        proposal.decidedAt = new Date(this.#now()).toISOString();
        if (input.note !== undefined)
            proposal.note = input.note;
        return proposal;
    }
    /** Consume an approved proposal exactly once, for the approved bytes and intent. */
    consume(proposalId, input) {
        const proposal = this.get(proposalId);
        this.#assertLive(proposal);
        if (proposal.status === 'consumed')
            throw new ProposalError('consumed', `${proposalId} was already executed`, proposalId);
        if (proposal.status === 'rejected')
            throw new ProposalError('rejected', `${proposalId} was rejected`, proposalId);
        if (proposal.status !== 'approved')
            throw new ProposalError('not_approved', `${proposalId} is ${proposal.status}`, proposalId);
        if (input.argsHash !== proposal.argsHash) {
            throw new ProposalError('stale_args', 'arguments changed after approval', proposalId);
        }
        if (input.intentHash !== undefined && input.intentHash !== proposal.intentHash) {
            throw new ProposalError('intent_mismatch', 'proposal intent differs from run intent', proposalId);
        }
        proposal.status = 'consumed';
        return proposal;
    }
    /** Mark a consumed proposal as verified by reading back the side effect. */
    verify(proposalId, input) {
        const proposal = this.get(proposalId);
        if (proposal.status !== 'consumed')
            throw new ProposalError('not_approved', `${proposalId} is ${proposal.status}, not consumed`, proposalId);
        proposal.status = 'verified';
        proposal.verifiedBy = input.by;
        proposal.verifiedAt = new Date(this.#now()).toISOString();
        return proposal;
    }
    /** Expire every live proposal past its TTL. */
    expire() {
        let count = 0;
        const now = this.#now();
        for (const proposal of this.#byId.values()) {
            if ((proposal.status === 'pending' || proposal.status === 'approved') && Date.parse(proposal.expiresAt) <= now) {
                proposal.status = 'expired';
                count += 1;
            }
        }
        return count;
    }
    /** Pending proposals, optionally for one run. */
    pending(runId) {
        return [...this.#byId.values()].filter((proposal) => proposal.status === 'pending' && (runId === undefined || proposal.runId === runId));
    }
    /** Counts by status. */
    stats() {
        const out = {};
        for (const proposal of this.#byId.values())
            out[proposal.status] = (out[proposal.status] ?? 0) + 1;
        return out;
    }
}
