import { useSession } from '#/features/auth/hooks';
import { createFileRoute, Link } from '@tanstack/react-router';
import { sessionQueryOptions } from '../features/auth/queries';

export const Route = createFileRoute( '/' )(
{
	beforeLoad: async ( { context } ) =>
	{
		await context.queryClient.ensureQueryData( sessionQueryOptions );
	},
	component: IndexPage
});

function IndexPage( )
{
	const { data: session } = useSession( );

	return (
		<div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8 lg:py-14">
			<section className="flex flex-col gap-6">
				<div className="flex flex-col gap-4">
					<p className="eyebrow">NetLogAnalyser</p>
					<h1 className="heading-1 max-w-2xl">
						Every packet,<br />
						<em>before it turns into noise.</em>
					</h1>
					<p className="body-text max-w-xl">
						Route packet ingestion, anomaly detection, and historical analysis through one product dashboard built for operators who need fast signal, not more clutter.
					</p>
					<div className="flex gap-3">
						{ session ? (
							<Link
								to="/dashboard"
								className="rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[12px] font-semibold text-[var(--color-ink)] no-underline transition-opacity hover:opacity-90"
							>
								Open dashboard
							</Link>
						) : (
							<>
								<Link
									to="/register"
									className="rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[12px] font-semibold text-white no-underline transition-opacity hover:opacity-90"
								>
									Get started
								</Link>
								<Link
									to="/login"
									className="rounded-md border border-border px-4 py-2.5 text-[12px] font-semibold text-text-secondary no-underline transition-colors hover:text-text-primary"
								>
									Sign in
								</Link>
							</>
						)}
					</div>
				</div>
			</section>

			<section className="grid gap-3 sm:grid-cols-3">
				<div className="panel p-5">
					<p className="section-title">Ingest</p>
					<h3 className="heading-3 mt-2">Single endpoint</h3>
					<p className="body-sm mt-2">Post packet batches and preserve capture context without extra configuration.</p>
				</div>
				<div className="panel p-5">
					<p className="section-title">Detect</p>
					<h3 className="heading-3 mt-2">Anomaly signals</h3>
					<p className="body-sm mt-2">Surface hot traffic, protocol drift, and suspicious spikes the moment they appear.</p>
				</div>
				<div className="panel p-5">
					<p className="section-title">Observe</p>
					<h3 className="heading-3 mt-2">Live + historical</h3>
					<p className="body-sm mt-2">Pivot from real-time streams to timeline queries without leaving the dashboard.</p>
				</div>
			</section>
		</div>
	)
}