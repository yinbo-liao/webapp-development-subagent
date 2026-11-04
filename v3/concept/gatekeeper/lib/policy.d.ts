/**
 * Effect-matrix evaluation.
 *
 * ADR-003: autonomy inside boundaries, DENY outside them. A guardrail is not a
 * suggestion; the caller must report which guardrails it verified, and a missing
 * verification fails closed. Approval is returned only where the matrix says ASK
 * (production effects owned by operator/approver roles).
 */
import type { Autonomy, DecisionContext, EffectMatrix, PolicyOutcome, RoleId } from './types.js';
/**
 * Effective autonomy for one (role, effect) pair: explicit entry, then the role's
 * wildcard, then the matrix default.
 */
export declare function autonomyFor(matrix: EffectMatrix, role: RoleId | string, effect: string): Autonomy;
/** Guardrails the matrix requires for one (role, effect) pair. */
export declare function requiredGuardrails(matrix: EffectMatrix, role: string, effect: string): readonly string[];
/**
 * Decide one tool call.
 *
 * Precedence: unknown role/effect (deny) → policy FORBIDDEN → kill switch →
 * ASK → guardrail verification → allow.
 */
export declare function decide(matrix: EffectMatrix, role: RoleId | string, effect: string, context?: DecisionContext): PolicyOutcome;
/**
 * Find a model/provider override anywhere in a tool-argument object. ADR-004
 * forbids runtime selection, so any such key is a policy violation rather than
 * an option to ignore.
 *
 * @returns the dotted path of the first offending key, or undefined.
 */
export declare function findModelOverride(value: unknown, path?: string, depth?: number): string | undefined;
