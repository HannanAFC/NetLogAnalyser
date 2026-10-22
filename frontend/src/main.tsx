import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from '@tanstack/react-router';
import { createRoot, hydrateRoot } from 'react-dom/client';
import { queryClient } from './lib/api/query-client';
import { ThemeProvider } from './lib/theme';
import { createAppRouter } from './router';
import './styles.css';
import '@fontsource-variable/inter';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import '@fontsource/ibm-plex-mono/700.css';

const router = createAppRouter( );

const rootElement = document.getElementById( 'app' )!;

const app = (
	<QueryClientProvider client={ queryClient }>
		<ThemeProvider>
			<RouterProvider router={ router } />
		</ThemeProvider>
	</QueryClientProvider>
);

if ( rootElement.hasChildNodes( ) )
{
	router.ssr = { manifest: undefined };

	// /login/ and /login are the same route
	const normalize = ( path: string ) => path.replace( /\/+$/, '' ) || '/';
	const prerenderedPath = normalize( window.location.pathname );

	router.load( ).then( ( ) =>
	{
		// <HeadContent /> re-creates these tags on hydration
		document.head.querySelectorAll( '[data-prerender]' ).forEach( ( el ) => el.remove( ) );

		// A route guard can redirect a returning visitor (e.g. /login -> /dashboard)
		// while loading. The markup then no longer matches the prerendered page,
		// so discard it and render client-side instead of hydrating.
		if ( normalize( router.state.location.pathname ) !== prerenderedPath )
		{
			rootElement.replaceChildren( );
			createRoot( rootElement ).render( app );
			return;
		}

		hydrateRoot( rootElement, app );
	} );
}
else
{
	createRoot( rootElement ).render( app );
}
