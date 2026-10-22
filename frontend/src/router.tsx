import { createRouter } from '@tanstack/react-router';
import { queryClient } from './lib/api/query-client';
import { routeTree } from './routeTree.gen';
import { ErrorComponent } from './components/error-component';
import type { RouterHistory } from '@tanstack/react-router';

// Shared by the browser entry (main.tsx) and the build-time prerender (entry-server.tsx)
export function createAppRouter( history?: RouterHistory, { scrollRestoration = true }: { scrollRestoration?: boolean } = { } )
{
	return createRouter(
	{
		routeTree,
		history,
		context: { queryClient },
		defaultPreload: 'intent',
		// Since we're using React Query, we don't want loader calls to ever be stale
		// This will ensure that the loader is always called when the route is preloaded or visited
		defaultPreloadStaleTime: 0,
		scrollRestoration,
		defaultErrorComponent: ( { error } ) => <ErrorComponent error={ error } />
	} );
}
