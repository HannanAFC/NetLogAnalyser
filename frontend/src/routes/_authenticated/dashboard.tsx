import { createFileRoute } from '@tanstack/react-router';
import { useSession, useLogout } from '../../features/auth/hooks';
import { Button } from '../../components/ui/button';

export const Route = createFileRoute( '/_authenticated/dashboard' )(
{
	component: DashboardPage
});

function DashboardPage( )
{
	const { data: session } = useSession( );
	const logout = useLogout( );

	return (
		<div className="mx-auto my-auto max-w-4xl px-6 py-12">
			<h1 className="heading-1 mb-1">Welcome, { session?.display_name }</h1>
			<p className="body-text mb-8">
				Live log data and analytics widgets go here.
			</p>

			<div className="grid grid-cols-1 gap-2 sm:grid-cols-2 mb-8">
				<div className="rounded-lg border bg-surface-card p-5 border-border relative overflow-hidden transition-[border-color,background] duration-150 hover:border-green-500/25 before:absolute before:inset-0 before:bg-green-500/3 before:opacity-0 before:transition-opacity before:duration-200 hover:before:opacity-100">
					<span className="font-mono text-[11px] font-medium text-green-500 tracking-[0.08em] uppercase">Analytics</span>
					<h3 className="text-sm font-medium text-text-primary mt-1.5">Traffic overview</h3>
					<p className="text-xs text-text-secondary leading-relaxed mt-1">Time-bucketed packet counts and protocol breakdowns.</p>
				</div>
				<div className="rounded-lg border bg-surface-card p-5 border-border relative overflow-hidden transition-[border-color,background] duration-150 hover:border-green-500/25 before:absolute before:inset-0 before:bg-green-500/3 before:opacity-0 before:transition-opacity before:duration-200 hover:before:opacity-100">
					<span className="font-mono text-[11px] font-medium text-green-500 tracking-[0.08em] uppercase">Live Feed</span>
					<h3 className="text-sm font-medium text-text-primary mt-1.5">WebSocket stream</h3>
					<p className="text-xs text-text-secondary leading-relaxed mt-1">Real-time log ingestion at <code className="code-inline">/ws/live</code>.</p>
				</div>
			</div>

			<Button variant="secondary" onClick={ ( ) => logout.mutate( ) } disabled={ logout.isPending }>
				{ logout.isPending ? 'Signing out…' : 'Sign out' }
			</Button>
		</div>
	);
}
