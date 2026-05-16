/**
 * Props for AuthForm component
 * @interface AuthFormProps
 */
export interface AuthFormProps {
  onSubmit: function;
}

/**
 * AuthForm component state
 */
export interface AuthFormState {
  isLoading: boolean;
  error: Error | null;
  data: unknown;
}
