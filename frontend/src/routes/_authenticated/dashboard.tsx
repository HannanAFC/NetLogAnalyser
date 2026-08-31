import { BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { useSession } from '#/features/auth/hooks';
import { createFileRoute, Link } from '@tanstack/react-router';
import { timeRangePresetSchema, timeRangeSearchSchema } from '#/lib/time-range/schema';
import { createUseTimeRange, setCustomRange } from '#/lib/time-range/use-time-range';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { TimeRangePicker } from '#/components/ui/time-range-picker';
import { SummaryStatCards } from '#/components/summary-stat-cards';
import { TimeseriesSparkline } from '#/components/dashboard/timeseries-sparkline';
import { TopAnomaliesPreview } from '#/components/dashboard/top-anomalies-preview';
import { useLiveFeed } from '#/features/live-feed/hooks';
import { LogTable } from '#/components/network-logs/log-table';
import { ConnectionStatusIndicator } from '#/components/live-feed/connection-status';
import { TableNoRecentsErrorMessage } from '#/components/ui/table-no-recents-error-message';
import { TableLoadingErrorMessage } from '#/components/ui/table-loading-error-message';

const dashboardSearchSchema = timeRangeSearchSchema.extend(
{
	preset: timeRangePresetSchema.default( '1h' ).catch( '1h' )
} )
.transform( ( data ) =>
{
	const hasStart = data.start !== undefined;
	const hasEnd   = data.end   !== undefined;

	if ( hasStart !== hasEnd )
	{
		return {
			preset: '1h',
			start:  undefined,
			end:    undefined
		};
	}

	return data;
} );

export const Route = createFileRoute( '/_authenticated/dashboard' )(
{
	component: DashboardPage,
	validateSearch: dashboardSearchSchema,
	head: ( ) => (
	{
		meta:
		[
			{
				title: 'Dashboard | NetLogAnalyser'
			},
			{
				name:    'robots',
				content: 'noindex, nofollow'
			}
		]
	} )
} );

const useTimeRange = createUseTimeRange( '/_authenticated/dashboard' );

function DashboardPage( )
{
	const { data: session } = useSession( );
	const [ range, setRange, search ] = useTimeRange( );
	const { entries, connectionStatus, isLoadingInitial, isInitialError } = useLiveFeed( );

	return (
		<PageWrapper>
			<Heading level="h1" className="max-w-2xl">Welcome back, { session?.display_name }.</Heading>
			<BodyText className='w-max max-w-full'>
				View everything at a glance, traffic summaries, top anomalies and your live ingest feed.
			</BodyText>

			<TimeRangePicker
				search={ search }
				setCustomRange={ ( start, end ) => setCustomRange( setRange, start, end ) }
				setPreset={ ( preset ) => setRange( { preset: preset } ) }
			/>
			<Heading level='h2'>Summary</Heading>
			<SummaryStatCards range={ range } />
			<Heading level='h2'>Packet volume</Heading>
			<TimeseriesSparkline range={ range } />
			<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
				<div className='flex flex-col gap-6'>
					<Heading level='h2'>Top anomalies</Heading>
					<TopAnomaliesPreview range={ range } />
				</div>
				<div className='flex flex-col gap-6'>
					<div className="flex items-center justify-between">
						<Heading level='h2'>Live feed</Heading>
						<ConnectionStatusIndicator status={ connectionStatus } />
					</div>
					<LogTable
						className='mt-0'
						isLoading={ isLoadingInitial }
						isError={ isInitialError }
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
						maxHeight='sm'
					/>
				</div>
			</div>
		</PageWrapper>
	);
}
