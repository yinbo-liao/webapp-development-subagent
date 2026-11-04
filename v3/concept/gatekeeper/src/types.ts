/**
 * Types shared by the gatekeeper core.
 *
 * The core is deliberately dependency-free: it consumes a parsed effect matrix
 * (JSON), returns decisions, and manages proposals and commit tokens. The DSH
 * plugin wires it to tools/pre-execute, ctx.tools.guard and ctx.approval.
 */

export type Autonomy = 'AUTO' | 'DRY_RUN' | 'ASK' | 'FORBIDDEN'

export type RoleId =
  | 'supervisor'
  | 'analyst'
  | 'architect'
  | 'builder'
  | 'verifier'
  | 'operator'
  | 'fde'
  | 'human'

export interface EffectSpec {
  readonly severity: number
  readonly description?: string
}

export interface RoleScope {
  readonly write_paths?: readonly string[]
}

export interface RoleSpec {
  readonly description?: string
  readonly tools?: readonly string[]
  readonly effects: Readonly<Record<string, Autonomy | '*' | string>>
  readonly scope?: RoleScope
  readonly profiles?: Readonly<Record<string, unknown>>
}

export interface EffectMatrix {
  readonly version: string | number
  readonly default: string
  readonly approval_model?: string
  readonly boundary_violation_action?: string
  readonly effects: Readonly<Record<string, EffectSpec>>
  readonly roles: Readonly<Record<string, RoleSpec>>
  readonly guardrails?: Readonly<Record<string, Readonly<Record<string, readonly string[]>>>>
}

export type DenyCode =
  | 'UNKNOWN_ROLE'
  | 'UNKNOWN_EFFECT'
  | 'POLICY_FORBIDDEN'
  | 'KILL_SWITCH'
  | 'GUARDRAIL_UNVERIFIED'
  | 'BOUNDARY_DENIED'
  | 'MODEL_OVERRIDE_FORBIDDEN'

export type PolicyOutcome =
  | { readonly kind: 'allow'; readonly mode: 'auto' | 'dry_run'; readonly guardrails: readonly string[] }
  | { readonly kind: 'ask'; readonly code: 'APPROVAL_REQUIRED'; readonly reason: string }
  | { readonly kind: 'deny'; readonly code: DenyCode; readonly reason: string }

export interface DecisionContext {
  readonly killSwitch?: boolean
  /** Guardrail names whose checks the caller actually performed and passed. */
  readonly guardrailsSatisfied?: readonly string[]
  readonly riskTier?: 'T0' | 'T1' | 'T2' | 'T3'
}