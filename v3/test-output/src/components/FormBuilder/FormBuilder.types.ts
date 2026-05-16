/**
 * Props for FormBuilder component
 * @interface FormBuilderProps
 */
export interface FormBuilderProps {
  schema: FormSchema;
}

/**
 * FormBuilder component state
 */
export interface FormBuilderState {
  isLoading: boolean;
  error: Error | null;
  data: unknown;
}
