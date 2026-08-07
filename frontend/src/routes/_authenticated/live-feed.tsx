import { createFileRoute, Link } from '@tanstack/react-router';
import { useLiveFeed } from '#/features/live-feed/hooks';
import { ConnectionStatusIndicator } from '#/components/live-feed/connection-status';
import { LogEntryRow } from '#/components/live-feed/log-entry-row';
import { getLogEntryKey } from '#/lib/logs/entry-key';
import { SkeletonLog } from '#/components/skeletons/skeleton-log';
import { BodyText, Heading } from '#/components/ui/heading';

export const Route = createFileRoute( '/_authenticated/live-feed' )(
{
  	component: LiveFeedPage,
  	head: ( ) => (
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/live-feed'
			}
		],
		meta:
		[
			{
				title: 'Live Feed | NetLogAnalyser'
			},
			{
				name: 'description',
				content: 'View your network logs in real-time.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Live Feed'
			},
			{
				name: 'og:description',
				content: 'View your network logs in real-time.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Live Feed'
			},
			{
				name: 'twitter:description',
				content: 'View your network logs in real-time.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/live-feed'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/live-feed'
			}
		]
	} )
} );

/** Grey placeholder rows that match the real table's row height, so the
 *  page doesn't jump when the initial fetch resolves. */
function SkeletonRows( { count = 20 }: { count?: number } )
{
	return (
		<>
			{ Array.from( { length: count }, ( _, i ) =>
			(
				<SkeletonLog key={ i } />
			) ) }
		</>
	);
}

function LiveFeedPage( )
{
	const { entries, connectionStatus, isLoadingInitial, isInitialError } = useLiveFeed( );

	return (
		<section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
			<div className="flex items-center justify-between">
				<div className='flex flex-col gap-4'>
					<Heading level='h1'>Live Feed</Heading>
					<BodyText>
						New log entries appear in real time - newest first.
					</BodyText>
				</div>
				<ConnectionStatusIndicator status={ connectionStatus } />
			</div>

			<div className="mt-8">
				{ isLoadingInitial && (
					<div className="overflow-x-auto rounded-lg border border-border">
						<table className="w-full text-left">
							<thead>
								<tr className="border-b border-border bg-surface-card text-xs font-medium text-text-secondary">
									<th className="px-3 py-2 font-medium">Time</th>
									<th className="px-3 py-2 font-medium">Source</th>
									<th className="px-3 py-2" />
									<th className="px-3 py-2 font-medium">Destination</th>
									<th className="px-3 py-2 font-medium">Protocol</th>
									<th className="px-3 py-2 text-right font-medium">Size</th>
									<th className="px-3 py-2 font-medium">Source country</th>
									<th className="px-3 py-2 font-medium">Destination country</th>
									<th className="px-3 py-2 font-medium">Anomaly</th>
								</tr>
							</thead>
							<tbody>
								<SkeletonRows />
							</tbody>
						</table>
					</div>
				) }

				{ isInitialError && !isLoadingInitial && (
					<div className="rounded-lg border border-danger/20 bg-danger/10 p-8 text-center text-sm text-danger">
						Couldn't load recent logs. The live feed will still start once connected.
					</div>
				) }

				{ !isLoadingInitial && !isInitialError && entries.length === 0 && (
					<div className="rounded-lg border border-border bg-surface-card p-8 text-center text-sm text-text-secondary">
						No log entries yet. Send traffic to your ingest endpoint —{' '}
						<Link to="/settings" className="font-medium text-accent underline underline-offset-2 hover:text-accent-strong">
							get your API key
						</Link>
						{' '}to see it here.
					</div>
				) }

				{ entries.length > 0 && (
					<div className="overflow-x-auto rounded-lg border border-border">
						<table className="w-full text-left tabular-nums">
							<thead>
								<tr className="border-b border-border bg-surface-card text-xs font-medium text-text-secondary">
									<th className="px-3 py-2 font-medium">Time</th>
									<th className="px-3 py-2 font-medium">Source</th>
									<th className="px-3 py-2" />
									<th className="px-3 py-2 font-medium">Destination</th>
									<th className="px-3 py-2 font-medium">Protocol</th>
									<th className="px-3 py-2 text-right font-medium">Size</th>
									<th className="px-3 py-2 font-medium">Source country</th>
									<th className="px-3 py-2 font-medium">Destination country</th>
									<th className="px-3 py-2 font-medium">Anomaly</th>
								</tr>
							</thead>
							<tbody>
								{ entries.map( ( entry ) => (
									<LogEntryRow key={ getLogEntryKey( entry ) } entry={ entry } />
								) ) }
							</tbody>
						</table>
					</div>
				) }
			</div>
		</section>
	);
}
