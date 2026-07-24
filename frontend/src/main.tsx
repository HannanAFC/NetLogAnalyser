import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createRouter } from '@tanstack/react-router';
import ReactDOM from 'react-dom/client';
import { queryClient } from './lib/api/query-client';
import { ThemeProvider } from './lib/theme';
import { routeTree } from './routeTree.gen';
import './styles.css';

// Set up a Router instance
const router = createRouter(
{
	routeTree,
	context: { queryClient },
	defaultPreload: 'intent',
	// Since we're using React Query, we don't want loader calls to ever be stale
	// This will ensure that the loader is always called when the route is preloaded or visited
	defaultPreloadStaleTime: 0,
	scrollRestoration: true
} );

// Register things for typesafety
declare module '@tanstack/react-router'
{
	interface Register
	{
		router: typeof router
	}
}

const rootElement = document.getElementById( 'app' )!;

if ( !rootElement.innerHTML )
{
	const root = ReactDOM.createRoot( rootElement );
	root.render(
		<QueryClientProvider client={ queryClient }>
			<ThemeProvider>
				<RouterProvider router={ router } />
			</ThemeProvider>
		</QueryClientProvider>
	);
}