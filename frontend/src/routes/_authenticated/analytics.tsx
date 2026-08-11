// routes/_authenticated/analytics.tsx
import { useMemo } from 'react';
import { createFileRoute } from '@tanstack/react-router';

import { SummaryStatCards } from '#/components/summary-stat-cards';
import { ProtocolBreakdown } from '#/components/analytics/protocol-breakdown';
import { TimeseriesBucketSelector } from '#/components/analytics/timeseries-bucket-selector';
import { TimeseriesChart } from '#/components/analytics/timeseries-chart';
import { TopTalkersTable } from '#/components/analytics/top-talkers-table';
import { TimeRangePicker } from '#/components/ui/time-range-picker';
import { timeRangeSearchSchema } from '#/lib/time-range/schema';
import { timeBucketSchema } from '#/features/analytics/schemas';
import { resolveBucket } from '#/lib/time-range/timeseries-bucket';
import { createUseTimeRange, setCustomRange } from '#/lib/time-range/use-time-range';
import type { TimeBucket } from '#/features/analytics/schemas';
import { BodyText, Heading } from '#/components/ui/heading';

const analyticsSearchSchema = timeRangeSearchSchema.extend(
{
	bucket: timeBucketSchema.optional( )
} );

export const Route = createFileRoute( '/_authenticated/analytics' )(
{
	validateSearch: analyticsSearchSchema,
	component:      AnalyticsPage
} );

const useTimeRange = createUseTimeRange( '/_authenticated/analytics' );

function AnalyticsPage( )
{
	const [ range, setRange ] = useTimeRange( );

	const search   = Route.useSearch( );
	const navigate = Route.useNavigate( );

	const resolved = useMemo(
		( ) => resolveBucket( range.start, range.end, search.bucket ),
		[ range.start, range.end, search.bucket ]
	);

	function handleBucketChange( bucket: TimeBucket | undefined )
	{
		navigate( { search: ( prev ) => ( { ...prev, bucket } ), replace: true } );
	}

	return (
		<div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8 flex flex-col gap-8">
			<section className="flex flex-col gap-4">
				<Heading level="h1" className="max-w-2xl">Analytics</Heading>
				<BodyText className='w-max max-w-full'>
					Get detailed insights via all the analytical avenues - with access to detailed time filters.
				</BodyText>
			</section>

			<section title='Time filters'>
			<TimeRangePicker
				search={ search }
				onChange={ ( start, end ) => setCustomRange( setRange, start, end ) }
			/>
			</section>

			<section className="flex flex-col gap-6">
				<Heading level='h2'>Summary</Heading>
				<SummaryStatCards range={ range } />
			</section>

			<section className="flex flex-col gap-6">
				<Heading level='h2'>Packet volume</Heading>
				<TimeseriesBucketSelector
					start={ range.start }
					end={ range.end }
					bucket={ search.bucket }
					resolvedBucket={ resolved.bucket }
					onChange={ handleBucketChange }
				/>
				<TimeseriesChart range={ range } bucket={ resolved.bucket } />
			</section>

			<div className="grid gap-6 md:grid-cols-2">
				<ProtocolBreakdown range={ range } />
				<TopTalkersTable range={ range } />
			</div>
		</div>
	);
}