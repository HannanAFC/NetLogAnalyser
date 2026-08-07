import { LogEntryRow } from '#/components/live-feed/log-entry-row';
import { SkeletonLog } from '#/components/skeletons/skeleton-log';
import { Button } from '#/components/ui/button';
import { Card, CardDescription } from '#/components/ui/card';
import { BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { useLogHistory } from '#/features/logs/hooks';
import { getLogEntryKey } from '#/lib/logs/entry-key';
import { createFileRoute, Link } from '@tanstack/react-router';

export const Route = createFileRoute( '/_authenticated/log-history' )(
{
  	component: LogHistoryPage,
	head: ( ) => (
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/log-history'
			}
		],
		meta:
		[
			{
				title: 'Log History | NetLogAnalyser'
			},
			{
				name: 'description',
				content: 'View historical network log data in full detail.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Log History'
			},
			{
				name: 'og:description',
				content: 'View historical network log data in full detail.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Log History'
			},
			{
				name: 'twitter:description',
				content: 'View historical network log data in full detail.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/log-history'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/log-history'
			}
		]
	} )
} );

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

function LogHistoryPage( )
{
	const { entries, isLoading, isError, hasNextPage, isFetchingNextPage, fetchNextPage } = useLogHistory( );

	function handleLoadMore(  )
	{
		if ( hasNextPage && !isFetchingNextPage )
		{
			fetchNextPage( );
		}
	}

 	return (
		<section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
			<div className='flex flex-col gap-4'>
				<Heading level='h1'>Log History</Heading>
				<BodyText>
					View historical network log data in full detail.
				</BodyText>
			</div>

			<div className="mt-5">
				{ isLoading && (
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

				{ isError && !isLoading && (
					<Card variant='critical'>
						<CardDescription variant='critical'>
							Couldn't load the log history
						</CardDescription>
					</Card>
				) }

				{ !isLoading && !isError && entries.length === 0 && (
					<Card variant='medium'>
						<CardDescription variant='medium'>
							No log entries yet. Send traffic to your ingest endpoint -{' '}
							<Link to="/settings" className="font-medium text-accent underline underline-offset-2 hover:text-accent-strong">
								get your API key
							</Link>
							{' '}to start sending logs now.
						</CardDescription>
					</Card>
				) }

				{ entries.length > 0 && (
					<div className='flex flex-col gap-4'>
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
						<Button
							className='mx-auto max-w-max'
							variant='secondary'
							disabled={ !hasNextPage }
							onClick={ handleLoadMore }
						>
							{ isFetchingNextPage ?
							(
								<>Loading</>
							)
							:
							(
								<>Load more</>
							) }
							
						</Button>
					</div>
				) }
			</div>
		</section>
	);
}
