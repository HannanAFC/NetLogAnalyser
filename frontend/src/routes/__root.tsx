import { ThemeToggle } from '#/components/ui/theme-toggle'
import { useSession } from '#/features/auth/hooks'
import { TanStackDevtools } from '@tanstack/react-devtools'
import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'

import { env } from '#/lib/env'
import '../styles.css'

export const Route = createRootRoute(
{
	component: RootComponent
} )

function RootComponent( )
{
	const { data: session } = useSession( );

	return (
		<div className="flex min-h-screen flex-col bg-[var(--color-paper)] text-text-primary">
			<header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
				<Link to="/" className="flex items-center gap-2.5 no-underline">
					<div className="h-2 w-2 rounded-sm bg-[var(--color-accent)]" />
					<span className="text-[14px] font-semibold tracking-[-0.02em] text-text-primary">
						NetLogAnalyser
					</span>
				</Link>

				<nav className="flex items-center gap-4">
					<ThemeToggle />
					{ session ? (
						<>
							<Link
								to="/dashboard"
								className="text-[13px] font-medium text-text-secondary no-underline transition-colors hover:text-text-primary"
							>
								Dashboard
							</Link>
							<Link
								to="/dashboard"
								className="rounded-md bg-[var(--color-accent)] px-3.5 py-2 text-[12px] font-semibold text-[var(--color-ink)] no-underline transition-opacity hover:opacity-90"
							>
								Open
							</Link>
						</>
					) : (
						<>
							<Link
								to="/login"
								className="text-[13px] font-medium text-text-secondary no-underline transition-colors hover:text-text-primary"
							>
								Sign in
							</Link>
							<Link
								to="/register"
								className="rounded-md bg-[var(--color-accent)] px-3.5 py-2 text-[12px] font-semibold text-white no-underline transition-opacity hover:opacity-90"
							>
								Get started
							</Link>
						</>
					)}
				</nav>
			</header>

			<div className="flex-1">
				<Outlet />
			</div>

			<footer className="mx-auto flex w-full max-w-6xl items-center justify-between border-t border-border px-4 py-5 sm:px-6 lg:px-8">
				<span className="text-[12px] text-text-tertiary">
					NetLogAnalyser · v0.1.0
				</span>
				<a href={ env.apiBaseUrl } className="text-[12px] font-medium text-text-tertiary no-underline transition-colors hover:text-text-secondary">
					API docs
				</a>
			</footer>

			<TanStackDevtools
				config={
				{
					position: 'bottom-right',
				}}
				plugins={
				[
					{
						name: 'TanStack Router',
						render: <TanStackRouterDevtoolsPanel />
					}
				]}
			/>
		</div>
	)
}
