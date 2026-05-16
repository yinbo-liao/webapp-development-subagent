/**
 * Props for Dashboard component
 * @interface DashboardProps
 */
export interface DashboardProps {
  data: DashboardData;
}

/**
 * Dashboard component state
 */
export interface DashboardState {
  isLoading: boolean;
  error: Error | null;
  data: unknown;
}
