/**
 * Types shared by the gatekeeper core.
 *
 * The core is deliberately dependency-free: it consumes a parsed effect matrix
 * (JSON), returns decisions, and manages proposals and commit tokens. The DSH
 * plugin wires it to tools/pre-execute, ctx.tools.guard and ctx.approval.
 */
export {};
