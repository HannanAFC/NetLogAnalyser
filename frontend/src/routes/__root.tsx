import { Outlet, createRootRoute, Link } from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { TanStackDevtools } from '@tanstack/react-devtools'
import { useSession } from '#/features/auth/hooks'

import '../styles.css'

export const Route = createRootRoute(
{
  	component: RootComponent
} )

function RootComponent( )
{
	const { data: session } = useSession( );

	return (
		<div className="flex min-h-screen flex-col">
			<header className="flex items-center justify-between px-6 py-7 border-b border-border max-w-215 mx-auto w-full">
				<Link to="/" className="flex items-center gap-2.5 no-underline">
					<div className="h-2.25 w-2.25 rounded-full bg-green-500 shadow-[0_0_10px_#22c55e,0_0_24px_rgba(34,197,94,0.12)] animate-[breathe_2.8s_ease-in-out_infinite]" />
					<span className="font-mono text-[15px] font-medium text-text-primary tracking-[-0.01em]">
						NetLogAnalyser
					</span>
				</Link>
				<nav className="flex items-center gap-5">
					{ session ? (
						<Link
							to="/dashboard"
							className="inline-flex items-center font-mono text-xs font-medium cursor-pointer border-none no-underline transition-[opacity,background] duration-150 tracking-[0.01em] px-4 py-2.25 gap-1.75 rounded-md bg-green-500 text-[#0a0f0a] hover:opacity-[0.88]"
						>
							Dashboard
						</Link>
					) : (
						<>
							<Link
								to="/login"
								className="font-mono text-[11px] font-medium text-text-tertiary no-underline hover:text-text-secondary transition-colors duration-150 uppercase tracking-wider"
							>
								Sign in
							</Link>
							<Link
								to="/register"
								className="inline-flex items-center font-mono text-xs font-medium cursor-pointer border-none no-underline transition-[opacity,background] duration-150 tracking-[0.01em] px-4 py-2.25 gap-1.75 rounded-md bg-green-500 text-[#0a0f0a] hover:opacity-[0.88]"
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

			<footer className="max-w-215 mx-auto w-full mt-16 pt-6 border-t border-border px-6 pb-10 flex items-center justify-between">
				<span className="font-mono text-[11px] text-text-tertiary">
					NetLogAnalyser &nbsp;·&nbsp; v0.1.0
				</span>
				<div className="flex gap-5">
					<a href={ `${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}` } className="text-xs text-text-tertiary no-underline hover:text-text-secondary transition-colors duration-150">
						API docs
					</a>
				</div>
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
