import { ThemeToggle } from '#/components/ui/theme-toggle';
import { useSession } from '#/features/auth/hooks';
import { TanStackDevtools } from '@tanstack/react-devtools';
import { createRootRoute, Link, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools';

import { NotFound } from '#/components/not-found';
import { Sidebar, SidebarProvider, useSidebar } from '#/components/sidebar';
import { Button } from '#/components/ui/button';
import { IndexLink } from '#/components/ui/index-link';
import { env } from '#/lib/env';
import { Menu } from 'lucide-react';
import '../styles.css';

export const Route = createRootRoute(
	{
		component: RootComponent,
		notFoundComponent: NotFound
	} );

function AuthenticatedHeader( )
{
	const { toggle } = useSidebar( );

	return (
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
	);
}

function RootComponent( )
{
	const { data: session } = useSession( );

	return (
		<SidebarProvider>
			<RootInner session={ session } />
		</SidebarProvider>
	);
}

function RootInner( { session }: { session: unknown } )
{
	const { open, close } = useSidebar();

	return (
		<>
			{ !!session && <Sidebar open={ open } onClose={ close } /> }
			<div className="flex min-h-screen flex-col bg-paper text-text-primary">
				<header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
					<div className="flex items-center gap-3">
						{ !!session && <AuthenticatedHeader /> }
						{ !session &&
						(
							<IndexLink />
						) }
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
									Sign in
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
						}
					] }
				/>
			</div>
		</>
	);
}
