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
			}
		],
		meta:
		[
			{
				title: 'NetLogAnalyser'
			},
			{
				name: 'description',
				content: 'Monitor, visualise, and analyse your network traffic in real time. Detect anomalies, track source geography, and investigate threats through a live dashboard.'
			},
			{
				name: 'keywords',
				content: 'network monitoring, log analysis, real-time traffic, anomaly detection, network security, packet analysis, threat detection'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Real-Time Network Log Analysis'
			},
			{
				name: 'og:site_name',
				content: 'NetLogAnalyser'
			},
			{
				name: 'og:description',
				content: 'Monitor, visualise, and analyse your network traffic in real time. Detect anomalies, track source geography, and investigate threats through a live dashboard.'
			},
			{
				name: 'og:type',
				content: 'website'
			},
			{
				name: 'twitter:card',
				content: 'summary'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Real-Time Network Log Analysis'
			},
			{
				name: 'twitter:description',
				content: 'Monitor, visualise, and analyse your network traffic in real time. Detect anomalies, track source geography, and investigate threats through a live dashboard.'
			}
		]
	} )
} );

function RootComponent( )
{
	const { data: session } = useSession( );

	return (
		<SidebarProvider>
			<RootLayout session={ session } />
		</SidebarProvider>
	);
}

function RootLayout( { session }: { session: unknown } )
{
	const { toggle, open, close } = useSidebar( );

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

				<footer className="mx-auto flex w-full max-w-6xl items-center justify-between border-t border-border px-4 py-5 sm:px-6 lg:px-8">
					<span className="text-xs text-text-tertiary">
						NetLogAnalyser · v0.1.0
					</span>
					<a href={ env.apiBaseUrl } className="text-xs font-medium text-text-tertiary no-underline transition-colors hover:text-text-secondary">
						API docs
					</a>
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
