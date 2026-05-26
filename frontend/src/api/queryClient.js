import { QueryClient } from '@tanstack/react-query';

/**
 * Shared QueryClient instance.
 *
 * Key decisions:
 * - staleTime 30s: dashboard data is considered fresh for 30 seconds after
 *   fetching, avoiding redundant requests when navigating between pages.
 * - retry 1: on failure, retry once before surfacing an error. The Axios
 *   interceptor already handles 401 → refresh transparently, so most
 *   transient errors should resolve on the first retry.
 * - refetchOnWindowFocus true (default): charts and tables refresh
 *   automatically when the user switches back to the tab — useful for a
 *   monitoring dashboard.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: true,
    },
    mutations: {
      retry: 0,
    },
  },
});

export default queryClient;