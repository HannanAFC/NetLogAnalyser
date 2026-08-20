import { createFileRoute, Link } from '@tanstack/react-router';
import { useLiveFeed } from '#/features/live-feed/hooks';
import { ConnectionStatusIndicator } from '#/components/live-feed/connection-status';
import { BodyText, Heading } from '#/components/ui/heading';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { LogTable } from '#/components/network-logs/log-table';
import { TableNoRecentsErrorMessage } from '#/components/ui/table-no-recents-error-message';
import { TableLoadingErrorMessage } from '#/components/ui/table-loading-error-message';

export const Route = createFileRoute( '/_authenticated/live-feed' )(
{
  	component: LiveFeedPage,
  	head: ( ) => (
	{
		meta:
		[
			{
				title: 'Live Feed | NetLogAnalyser'
			},
			{
				name:    'robots',
				content: 'noindex, nofollow'
			}
		]
	} )
} );

function LiveFeedPage( )
{
	const { entries, connectionStatus, isLoadingInitial, isInitialError } = useLiveFeed( );

	return (
		<PageWrapper>
			<div className="flex items-center justify-between">
				<Heading level='h1'>Live Feed</Heading>
				<ConnectionStatusIndicator status={ connectionStatus } />
			</div>
			<BodyText className="mt-2">
				New log entries appear in real time - newest first.
			</BodyText>
			<LogTable
				isLoading={isLoadingInitial}
				isError={isInitialError}
				loadingErrorMessage={ <TableLoadingErrorMessage>Couldn't load recent logs. The live feed will still start once connected.</TableLoadingErrorMessage> }
				noRecentLogsErrorMessage={
					<TableNoRecentsErrorMessage>
						No log entries yet. Send traffic to your ingest endpoint -{' '}
						<Link to="/settings" className="font-medium text-accent underline underline-offset-2 hover:text-accent-strong">
							get your API key
						</Link>
						{' '}to start sending logs now.
					</TableNoRecentsErrorMessage>
				}
				entries={entries}
			/>
		</PageWrapper>
	);
}
