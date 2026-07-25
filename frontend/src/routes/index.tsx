import { Card } from '#/components/ui/card';
import { BodySm, BodyText, Eyebrow, Heading, SectionTitle } from '#/components/ui/heading';
import { useSession } from '#/features/auth/hooks';
import { sessionQueryOptions } from '#/features/auth/queries';
import { createFileRoute, Link } from '@tanstack/react-router';

export const Route = createFileRoute( '/' )(
	{
		beforeLoad: async( { context } ) =>
		{
			await context.queryClient.ensureQueryData( sessionQueryOptions );
		},
		component: IndexPage
	} );

function IndexPage( )
{
	const { data: session } = useSession( );

	return (
		<div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8 lg:py-14">
			<section className="flex flex-col gap-6">
				<div className="flex flex-col gap-4">
					<Eyebrow>NetLogAnalyser</Eyebrow>
					<Heading level="h1" className="max-w-2xl">
						Every packet,<br />
						<em>before it turns into noise.</em>
					</Heading>
					<BodyText className="max-w-xl">
						Route packet ingestion, anomaly detection, and historical analysis through one product dashboard built for operators who need fast signal, not more clutter.
					</BodyText>
					<div className="flex gap-3">
						{ session ? (
							<Link
								to="/dashboard"
								className="rounded-md bg-accent px-4 py-2.5 text-xs font-semibold text-ink no-underline transition-opacity hover:opacity-90"
							>
								Open dashboard
							</Link>
						) : (
							<>
								<Link
									to="/register"
									className="rounded-md bg-accent px-4 py-2.5 text-xs font-semibold text-ink no-underline transition-opacity hover:opacity-90"
								>
									Get started
								</Link>
								<Link
									to="/login"
									className="rounded-md border border-border px-4 py-2.5 text-xs font-semibold text-text-secondary no-underline transition-colors hover:text-text-primary"
								>
									Sign in
								</Link>
							</>
						)}
					</div>
				</div>
			</section>

			<section className="grid gap-3 sm:grid-cols-3">
				<Card>
					<SectionTitle>Ingest</SectionTitle>
					<Heading level="h3" className="mt-2">Single endpoint</Heading>
					<BodySm className="mt-2">Post packet batches and preserve capture context without extra configuration.</BodySm>
				</Card>
				<Card>
					<SectionTitle>Detect</SectionTitle>
					<Heading level="h3" className="mt-2">Anomaly signals</Heading>
					<BodySm className="mt-2">Surface hot traffic, protocol drift, and suspicious spikes the moment they appear.</BodySm>
				</Card>
				<Card>
					<SectionTitle>Observe</SectionTitle>
					<Heading level="h3" className="mt-2">Live + historical</Heading>
					<BodySm className="mt-2">Pivot from real-time streams to timeline queries without leaving the dashboard.</BodySm>
				</Card>
			</section>
		</div>
	);
}
