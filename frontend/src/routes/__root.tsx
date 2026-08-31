import { ThemeToggle } from '#/components/ui/theme-toggle';
import { useSession } from '#/features/auth/hooks';
import { TanStackDevtools } from '@tanstack/react-devtools';
import { createRootRoute, HeadContent, Link, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools';
import { FormDevtoolsPanel } from '@tanstack/react-form-devtools';
import { ReactQueryDevtoolsPanel } from '@tanstack/react-query-devtools';
import { TableDevtoolsPanel } from '@tanstack/react-table-devtools';
import { NotFound } from '#/components/not-found';
import { Sidebar, SidebarProvider, useSidebar } from '#/components/sidebar';
import { Button } from '#/components/ui/button';
import { IndexLink } from '#/components/ui/index-link';
import { env } from '#/lib/env';
import { Menu } from 'lucide-react';
import '../styles.css';
import { OverlayProvider } from '#/lib/overlay/overlay-context';
import { ErrorComponent } from '#/components/error-component';
import { useAppVersion } from '#/features/health/hooks';

export const Route = createRootRoute(
{
	component: ( ) =>
	(
		<>
			<HeadContent />
			<RootComponent />
		</>
	),
	notFoundComponent: NotFound,
	errorComponent:    ErrorComponent,
	head: ( ) => (
	{
		links:
		[
			{
				rel: 'icon',
				type: 'image/png',
				href: '/favicon-96x96.png',
				sizes: '96x96'
			},
			{
				rel: 'icon',
				type: 'image/svg+xml',
				href: 'favicon.svg'
			},
			{
				rel: 'shortcut icon',
				href: 'favicon.ico'
			},
			{
				rel: 'apple-touch-icon',
				sizes: '180x180',
				href: 'apple-touch-icon.png'
			},
			{
				rel: 'manifest',
				href: 'manifest.json'
			},
			{
				rel: 'stylesheet',
				href: 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap'
			},
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/'
			}
		],
		meta:
		[
			{
				title: 'NetLogAnalyser - Real-time network log analysis'
			},
			{
				name: 'description',
				content: 'Real-time network log ingestion, anomaly detection, and live dashboards.'
			},
			{
				name: 'keywords',
				content: 'network monitoring, log analysis, real-time traffic, anomaly detection, network security, packet analysis, threat detection'
			},
			{
				name: 'og:type',
				content: 'website'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Real-Time Network Log Analysis'
			},
			{
				name: 'og:description',
				content: 'Real-time network log ingestion, anomaly detection, and live dashboards.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/'
			},
			{
				name: 'og:image',
				content: 'og-image.png'
			},
			{
				name: 'twitter:card',
				content: 'summary_large_image'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Real-Time Network Log Analysis'
			},
			{
				name: 'twitter:description',
				content: 'Real-time network log ingestion, anomaly detection, and live dashboards.'
			},
			{
				name: 'twitter:image',
				content: 'og-image.png'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/'
			}
		]
	} )
} );

function RootComponent( )
{
	const { data: session } = useSession( );

	return (
		<OverlayProvider>
			<SidebarProvider>
				<RootLayout session={ session } />
			</SidebarProvider>
		</OverlayProvider>
	);
}

function RootLayout( { session }: { session: unknown } )
{
	const { toggle, open, close } = useSidebar( );
	const appVersion = useAppVersion( );

	return (
		<>
			{ !!session && <Sidebar open={ open } onClose={ close } /> }
			<div className="flex min-h-screen flex-col bg-paper text-text-primary">
				<header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
					<div className="flex items-center gap-3">
						{ !!session &&
						<>
							<Button
								type="button"
								onClick={ toggle }
								aria-label="Toggle navigation"
								variant='ghost'
							>
								<Menu className="h-5 w-5" />
							</Button>
							<IndexLink />
						</>
						}
						{ !session && <IndexLink /> }
					</div>

					<nav className="flex items-center gap-4">
						<ThemeToggle />
						{ !session &&
						(
							<>
								<Link
									to="/login"
									className="text-sm font-medium text-text-secondary no-underline transition-colors hover:text-text-primary"
								>
									Login
								</Link>
								<Link
									to="/register"
									className="rounded-md bg-accent px-3.5 py-2 text-xs font-semibold text-ink no-underline transition-opacity hover:opacity-90"
								>
									Get started
								</Link>
							</>
						) }
					</nav>
				</header>

				<div className="flex-1">
					<Outlet />
				</div>

				<footer className="mx-auto flex flex-col md:flex-row gap-4 w-full max-w-6xl items-center justify-between border-t border-border px-4 py-5 sm:px-6 lg:px-8">
					<div>
						<span className="text-xs text-text-tertiary">
							NetLogAnalyser · v{ appVersion }
						</span>
					</div>
					<div className='flex gap-4'>
						<Link to='/legal' className='text-xs font-medium text-text-tertiary no-underline transition-colors hover:text-text-secondary'>
							Legal
						</Link>
						<a href={ env.apiBaseUrl } className="text-xs font-medium text-text-tertiary no-underline transition-colors hover:text-text-secondary">
							API docs
						</a>
					</div>
				</footer>

				<TanStackDevtools
					config={
					{
						position: 'bottom-right'
					} }
					plugins={
					[
						{
							name:   'TanStack Router',
							render: <TanStackRouterDevtoolsPanel />
						},
						{
							name:   'TanStack Query',
							render: <ReactQueryDevtoolsPanel />
						},
						{
							name:   'TanStack Form',
							render: <FormDevtoolsPanel />
						},
						{
							name:   'TanStack Table',
							render: <TableDevtoolsPanel />
						}
					] }
				/>
			</div>
		</>
	);
}
