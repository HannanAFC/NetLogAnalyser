import { LogTable } from '#/components/network-logs/log-table';
import { Button } from '#/components/ui/button';
import { BodyText, Heading } from '#/components/ui/heading';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { TableLoadingErrorMessage } from '#/components/ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '#/components/ui/table-no-recents-error-message';
import { useLogHistory } from '#/features/logs/hooks';
import { createFileRoute, Link } from '@tanstack/react-router';

export const Route = createFileRoute( '/_authenticated/log-history' )(
{
  	component: LogHistoryPage,
	head: ( ) => (
	{
		meta:
		[
			{
				title: 'Log History | NetLogAnalyser'
			},
			{
				name:    'robots',
				content: 'noindex, nofollow'
			}
		]
	} )
} );

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
		<PageWrapper>
			<Heading level='h1'>Log History</Heading>
			<BodyText className="mt-2">
				View historical network log data in full detail.
			</BodyText>
			<div className='flex flex-col items-center gap-8'>
				<LogTable
					className="w-full"
					isLoading={ isLoading }
					isError={ isError }
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
					entries={ entries }
				/>
				{ entries.length > 0 &&
				(
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
				) }
			</div>
		</PageWrapper>
	);
}
