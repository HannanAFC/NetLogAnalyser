import { LoadingErrorMessage } from '#/components/logs/loading-error-message';
import { NoRecentLogsErrorMessage } from '#/components/logs/no-recent-logs-error-message';
import { LogTable } from '#/components/network-logs/log-table';
import { Button } from '#/components/ui/button';
import { BodyText, Heading } from '#/components/ui/heading';
import { useLogHistory } from '#/features/logs/hooks';
import { createFileRoute } from '@tanstack/react-router';

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
			<div className='flex flex-col items-center gap-8'>
				<LogTable
					className="w-full"
					isLoading={ isLoading }
					isError={ isError }
					loadingErrorMessage={ <LoadingErrorMessage /> }
					noRecentLogsErrorMessage={ <NoRecentLogsErrorMessage /> }
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
		</section>
	);
}
