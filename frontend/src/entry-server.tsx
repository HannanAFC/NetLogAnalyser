import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createMemoryHistory } from '@tanstack/react-router';
import { renderToString } from 'react-dom/server';
import { queryClient } from './lib/api/query-client';
import { sessionQueryKey } from './lib/auth/session-key';
import { ThemeProvider } from './lib/theme';
import { createAppRouter } from './router';

/**
 * Build-time render of a public route. Called by scripts/prerender.mjs.
 * The visitor is always anonymous here, so the session is set as null
 * to stop any route guard from calling the API during the build.
 */
export async function render( url: string )
{
	queryClient.clear( );
	queryClient.setQueryData( sessionQueryKey, null );

	const router = createAppRouter(
		createMemoryHistory( { initialEntries: [ url ] } ),
		// The server would inline a restore-scroll <script> that the client doesn't render
		{ scrollRestoration: false }
	);
	await router.load( );

	const html = renderToString(
		<QueryClientProvider client={ queryClient }>
			<ThemeProvider>
				<RouterProvider router={ router } />
			</ThemeProvider>
		</QueryClientProvider>
	);

	return { html, pathname: router.state.location.pathname };
}
