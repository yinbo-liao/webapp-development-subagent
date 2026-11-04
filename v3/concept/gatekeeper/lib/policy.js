/**
 * Effect-matrix evaluation.
 *
 * ADR-003: autonomy inside boundaries, DENY outside them. A guardrail is not a
 * suggestion; the caller must report which guardrails it verified, and a missing
 * verification fails closed. Approval is returned only where the matrix says ASK
 * (production effects owned by operator/approver roles).
 */
const AUTONOMY = new Set(['AUTO', 'DRY_RUN', 'ASK', 'FORBIDDEN']);
/** Coerce an untyped matrix value into a valid autonomy, failing closed. */
function normalize(value) {
    return typeof value === 'string' && AUTONOMY.has(value) ? value : 'FORBIDDEN';
}
/** Resolve the role spec, or undefined when the role is unknown. */
function roleSpec(matrix, role) {
    const spec = matrix.roles[role];
    return spec !== undefined && typeof spec === 'object' ? spec : undefined;
}
/**
 * Effective autonomy for one (role, effect) pair: explicit entry, then the role's
 * wildcard, then the matrix default.
 */
export function autonomyFor(matrix, role, effect) {
    const spec = roleSpec(matrix, role);
    if (spec === undefined)
        return 'FORBIDDEN';
    const explicit = spec.effects[effect];
    if (explicit !== undefined)
        return normalize(explicit);
    const wildcard = spec.effects['*'];
    if (wildcard !== undefined)
        return normalize(wildcard);
    return normalize(matrix.default);
}
/** Guardrails the matrix requires for one (role, effect) pair. */
export function requiredGuardrails(matrix, role, effect) {
    const list = matrix.guardrails?.[role]?.[effect];
    return Array.isArray(list) ? list : [];
}
/** Build a deny outcome. */
function deny(code, reason) {
    return { kind: 'deny', code, reason };
}
/**
 * Decide one tool call.
 *
 * Precedence: unknown role/effect (deny) → policy FORBIDDEN → kill switch →
 * ASK → guardrail verification → allow.
 */
export function decide(matrix, role, effect, context = {}) {
    const spec = roleSpec(matrix, role);
    if (spec === undefined)
        return deny('UNKNOWN_ROLE', `unknown role "${role}"`);
    const effectSpec = matrix.effects[effect];
    if (effectSpec === undefined)
        return deny('UNKNOWN_EFFECT', `unknown effect "${effect}"`);
    const autonomy = autonomyFor(matrix, role, effect);
    if (autonomy === 'FORBIDDEN') {
        return deny('POLICY_FORBIDDEN', `${role} may not perform ${effect} (severity ${effectSpec.severity})`);
    }
    if (context.killSwitch === true && effectSpec.severity > 0) {
        return deny('KILL_SWITCH', `kill switch active: ${effect} is frozen`);
    }
    if (autonomy === 'ASK') {
        return {
            kind: 'ask',
            code: 'APPROVAL_REQUIRED',
            reason: `${role} requires human approval for ${effect}`,
        };
    }
    const required = requiredGuardrails(matrix, role, effect);
    const satisfied = new Set(context.guardrailsSatisfied ?? []);
    const missing = required.filter((name) => !satisfied.has(name));
    if (missing.length > 0) {
        return deny('GUARDRAIL_UNVERIFIED', `unverified guardrail(s) for ${role}/${effect}: ${missing.join(', ')}`);
    }
    return {
        kind: 'allow',
        mode: autonomy === 'DRY_RUN' ? 'dry_run' : 'auto',
        guardrails: required,
    };
}
const MODEL_KEYS = new Set(['model', 'provider', 'modelId', 'model_id', 'route', 'modelRoute']);
/**
 * Find a model/provider override anywhere in a tool-argument object. ADR-004
 * forbids runtime selection, so any such key is a policy violation rather than
 * an option to ignore.
 *
 * @returns the dotted path of the first offending key, or undefined.
 */
export function findModelOverride(value, path = '', depth = 0) {
    if (depth > 6 || value === null || typeof value !== 'object')
        return undefined;
    if (Array.isArray(value)) {
        for (let index = 0; index < value.length; index += 1) {
            const found = findModelOverride(value[index], `${path}[${index}]`, depth + 1);
            if (found !== undefined)
                return found;
        }
        return undefined;
    }
    for (const [key, nested] of Object.entries(value)) {
        const current = path === '' ? key : `${path}.${key}`;
        if (MODEL_KEYS.has(key))
            return current;
        const found = findModelOverride(nested, current, depth + 1);
        if (found !== undefined)
            return found;
    }
    return undefined;
}
