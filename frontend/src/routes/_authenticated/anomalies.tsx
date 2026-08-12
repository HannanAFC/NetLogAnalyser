import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

import { AnomaliesTable } from '#/components/anomalies/anomalies-table';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { TimeRangePicker } from '#/components/ui/time-range-picker';
import { timeRangeSearchSchema } from '#/lib/time-range/schema';
import { createUseTimeRange, setCustomRange } from '#/lib/time-range/use-time-range';
import { useEffect, useMemo, useRef, useState } from 'react';
import { BodyText, Heading } from '#/components/ui/heading';

const anomaliesSearchSchema = timeRangeSearchSchema.extend(
{
	min_score: z.number( ).min( 0 ).max( 1 ).default( 0.5 )
} );

export const Route = createFileRoute( '/_authenticated/anomalies' )(
{
	validateSearch: anomaliesSearchSchema,
	component:      AnomaliesPage
} );

const useTimeRange = createUseTimeRange( '/_authenticated/anomalies' );

function AnomaliesPage( )
{
	const [ range, setRange ] = useTimeRange( );
	const search   = Route.useSearch( );
	const navigate = Route.useNavigate( );
	const [ debounceValue, setDebounceValue ] = useState< number >( search.min_score );
	const mountedRef = useRef( false );

	const sliderStyle = useMemo( ( ) =>
	{
		const pct = debounceValue * 100;
		let fill = 'var( --color-low )';
		if ( debounceValue > 0.66 ) fill = 'var( --color-critical )';
		else if ( debounceValue > 0.33 ) fill = 'var( --color-medium )';

		return {
			'--range-pct': `${ pct }%`,
			'--range-fill': fill
		} as React.CSSProperties;
	}, [ debounceValue ] );

	useEffect( ( ) =>
	{
		if ( !mountedRef.current )
		{
			mountedRef.current = true;
			return;
		}

		const handler = setTimeout( ( ) =>
		{
			changeMinScore( debounceValue );
		}, 500 );

		return ( ) => clearTimeout( handler );
	}, [ debounceValue, changeMinScore ] );

	function changeMinScore( value: number )
	{
		navigate( { search: ( prev ) => ( { ...prev, min_score: value } ), replace: true } );
	}

	return (
		<PageWrapper>
			<Heading level='h1'>Anomalies</Heading>
			<BodyText className="mt-2">
				View all detected anomalies - filter by time range and minimum anomaly score.
			</BodyText>
			<div className="flex flex-row gap-4 flex-wrap">
				<TimeRangePicker
					className='block max-w-max'
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
						value={ debounceValue }
						onChange={ ( e ) => setDebounceValue( Number( e.target.value ) ) }
					/>
					<span>{ debounceValue.toFixed( 2 ) }</span>
				</label>
			</div>

			<AnomaliesTable filter={ { ...range, min_score: search.min_score, limit: 25 } } />
		</PageWrapper>
	);
}