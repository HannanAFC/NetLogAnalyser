import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

import { AnomaliesTable } from '#/components/anomalies/anomalies-table';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { TimeRangePicker } from '#/components/ui/time-range-picker';
import { timeRangePresetSchema, timeRangeSearchSchema } from '#/lib/time-range/schema';
import { createUseTimeRange, setCustomRange } from '#/lib/time-range/use-time-range';
import { useEffect, useMemo, useRef, useState } from 'react';
import { BodyText, Heading } from '#/components/ui/heading';
import { useDebounce } from '#/lib/utils';

const anomaliesSearchSchema = timeRangeSearchSchema.extend(
{
	min_score: z.number( ).min( 0 ).max( 1 ).default( 0.5 )
} )
.transform( ( data ) =>
{
	const hasStart = data.start !== undefined;
	const hasEnd   = data.end   !== undefined;

	if ( hasStart !== hasEnd )
	{
		return {
			preset:    timeRangePresetSchema.parse( '24h' ),
			min_score: data.min_score,
			start:     undefined,
			end:       undefined
		};
	}

	return data;
} );

export const Route = createFileRoute( '/_authenticated/anomalies' )(
{
	validateSearch: anomaliesSearchSchema,
	component:      AnomaliesPage,
	head: ( ) => (
	{
		meta:
		[
			{
				title: 'Anomalies | NetLogAnalyser'
			},
			{
				name:    'robots',
				content: 'noindex, nofollow'
			}
		]
	} )
} );

const useTimeRange = createUseTimeRange( '/_authenticated/anomalies' );

function AnomaliesPage( )
{
	const [ range, setRange ] = useTimeRange( );
	const search   = Route.useSearch( );
	const navigate = Route.useNavigate( );
	const [ minScore, setMinScore ] = useState( search.min_score );
	const debouncedMinScore = useDebounce( minScore, 500 );
	const mountedRef = useRef( false );

	const sliderStyle = useMemo( ( ) =>
	{
		const pct = minScore * 100;
		let fill = 'var( --color-low )';
		if ( minScore > 0.66 ) fill = 'var( --color-critical )';
		else if ( minScore > 0.33 ) fill = 'var( --color-medium )';

		return {
			'--range-pct': `${ pct }%`,
			'--range-fill': fill
		} as React.CSSProperties;
	}, [ minScore ] );

	useEffect( ( ) =>
	{
		if ( !mountedRef.current )
		{
			mountedRef.current = true;
			return;
		}

		navigate( { search: ( prev ) => ( { ...prev, min_score: debouncedMinScore } ), replace: true } );

	}, [ debouncedMinScore, navigate ] );

	return (
		<PageWrapper>
			<Heading level='h1'>Anomalies</Heading>
			<BodyText>
				View all detected anomalies - filter by time range and minimum anomaly score.
			</BodyText>
			<div className="flex flex-row gap-4 flex-wrap">
				<TimeRangePicker
					search={ search }
					onChange={ ( start, end ) => setCustomRange( setRange, start, end ) }
				/>
				<label className="flex items-center gap-2 text-sm text-nowrap">
					Min score
					<input
						type="range"
						className="range-slider w-32"
						style={ sliderStyle }
						min={ 0 }
						max={ 1 }
						step={ 0.05 }
						value={ minScore }
						onChange={ ( e ) => setMinScore( Number( e.target.value ) ) }
					/>
					<span>{ minScore.toFixed( 2 ) }</span>
				</label>
			</div>

			<AnomaliesTable filter={ { ...range, min_score: search.min_score, limit: 25 } } />
		</PageWrapper>
	);
}