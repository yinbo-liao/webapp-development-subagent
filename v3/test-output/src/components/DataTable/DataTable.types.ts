/**
 * Props for DataTable component
 * @interface DataTableProps
 */
export interface DataTableProps {
  rows: Array<Record>;
}

/**
 * DataTable component state
 */
export interface DataTableState {
  isLoading: boolean;
  error: Error | null;
  data: unknown;
}
