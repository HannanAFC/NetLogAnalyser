import { createFileRoute } from '@tanstack/react-router';
import { useLiveFeed } from '#/features/live-feed/hooks';
import { ConnectionStatusIndicator } from '#/components/live-feed/connection-status';
import { BodyText, Heading } from '#/components/ui/heading';
import { LogTable } from '#/components/network-logs/log-table';
import { LoadingErrorMessage } from '#/components/live-feed/loading-error-message';
import { NoRecentLogsErrorMessage } from '#/components/live-feed/no-recent-logs-error-message';

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
			<LogTable
				isLoading={isLoadingInitial}
				isError={isInitialError}
				loadingErrorMessage={<LoadingErrorMessage />}
				noRecentLogsErrorMessage={<NoRecentLogsErrorMessage />}
				entries={entries}
			/>
		</section>
	);
}
