import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

import { AnomaliesTable } from '#/components/anomalies/anomalies-table';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { TimeRangePicker } from '#/components/ui/time-range-picker';
import { timeRangeSearchSchema } from '#/lib/time-range/schema';
import { createUseTimeRange, setCustomRange } from '#/lib/time-range/use-time-range';

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

	function handleMinScoreChange( value: number )
	{
		navigate( { search: ( prev ) => ( { ...prev, min_score: value } ), replace: true } );
	}

	return (
		<PageWrapper>
			<div className="flex flex-wrap items-center gap-4">
				<TimeRangePicker
					search={ search }
					onChange={ ( start, end ) => setCustomRange( setRange, start, end ) }
				/>
				<label className="flex items-center gap-2 text-sm">
					Min score
					<input
						type="range"
						min={ 0 }
						max={ 1 }
						step={ 0.05 }
						value={ search.min_score }
						onChange={ ( e ) => handleMinScoreChange( Number( e.target.value ) ) }
					/>
					<span>{ search.min_score.toFixed( 2 ) }</span>
				</label>
			</div>

			<AnomaliesTable filter={ { ...range, min_score: search.min_score, limit: 25 } } />
		</PageWrapper>
	);
}