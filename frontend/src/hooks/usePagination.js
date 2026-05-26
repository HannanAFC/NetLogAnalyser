import { useState } from 'react';

/**
 * usePagination
 *
 * Manages page + limit state and provides helpers for navigating.
 * Designed to be used with TanStack Query — include { page, limit } in
 * your queryKey so data refetches automatically when the page changes.
 *
 * @param {{ initialPage?: number, initialLimit?: number }} options
 */
export function usePagination({ initialPage = 1, initialLimit = 25 } = {}) {
  const [page, setPage] = useState(initialPage);
  const [limit, setLimit] = useState(initialLimit);

  return {
    page,
    limit,
    setPage,
    setLimit,
    nextPage: () => setPage((p) => p + 1),
    prevPage: () => setPage((p) => Math.max(1, p - 1)),
    // Reset to page 1 — call this whenever a filter changes so you don't land
    // on a page that no longer exists.
    reset: () => setPage(1),
  };
}