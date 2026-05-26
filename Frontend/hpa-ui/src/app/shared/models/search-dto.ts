export type FilterOperator = 'eq' | 'contains';

export type FilterValue = string | number | boolean | null;

export interface Filter<F extends string = string> {
  field: F;
  operator: FilterOperator;
  value: FilterValue;
}

export interface Sorter<F extends string = string> {
  field: F;
  direction: 'asc' | 'desc';
}

export interface Pagination {
  page: number;
  pageSize: number;
}

export interface SearchDTO<F extends string = string> {
  filters: Filter<F>[];
  sorters: Sorter<F>[];
  pagination: Pagination;
}
