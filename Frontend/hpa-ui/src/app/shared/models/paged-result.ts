export interface PagedResult<T> {
  results: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalElements: number;
    totalPages: number;
  };
}
