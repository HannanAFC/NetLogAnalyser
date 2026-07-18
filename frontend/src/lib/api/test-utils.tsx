import type { QueryClient } from '@tanstack/react-query';
import { QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

export function wrapperFor( queryClient: QueryClient )
{
	return ( { children }: { children: ReactNode } ) => (
		<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
	);
}
