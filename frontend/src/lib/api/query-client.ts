import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient(
{
    defaultOptions:
    {
        queries:
        {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: ( failureCount, error ) =>
            {
                const status = ( error as { response?: { status?: number } } ).response?.status;
                // Don't burn retries on errors that won't resolve by retrying.
                if ( status === 401 || status === 403 || status === 404 ) return false;
                return failureCount < 2;
            }
        },
        mutations:
        {
            retry: false
        }
    }
});
