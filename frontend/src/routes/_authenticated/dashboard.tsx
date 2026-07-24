import { createFileRoute } from '@tanstack/react-router';
import { Button } from '../../components/ui/button';
import { useLogout, useSession } from '../../features/auth/hooks';

export const Route = createFileRoute( '/_authenticated/dashboard' )(
	{
		component: DashboardPage
	} );

function DashboardPage( )
{
	const { data: session } = useSession( );
	const logout = useLogout( );

	return (
		<div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
			<section className="flex flex-col gap-4">
				<p className="eyebrow">Operator dashboard</p>
				<h1 className="heading-1 max-w-2xl">Welcome back, { session?.display_name }.</h1>
				<p className="body-text max-w-xl">
					Live packet flow and anomaly context surfaced for faster triage and cleaner reporting.
				</p>
			</section>

			<section className="mt-8 grid gap-3 sm:grid-cols-2">
				<div className="panel p-5">
					<p className="section-title">Analytics</p>
					<h3 className="heading-3 mt-2">Traffic overview</h3>
					<p className="body-sm mt-2">Time-bucketed packet counts and protocol breakdowns with geo enrichment.</p>
				</div>
				<div className="panel p-5">
					<p className="section-title">Session</p>
					<h3 className="heading-3 mt-2">Controls</h3>
					<p className="body-sm mt-2 mb-4">Signed in as { session?.email }.</p>
					<Button variant="secondary" onClick={ ( ) => logout.mutate( ) } disabled={ logout.isPending }>
						{ logout.isPending ? 'Signing out…' : 'Sign out' }
					</Button>
				</div>
			</section>
		</div>
	);
}
