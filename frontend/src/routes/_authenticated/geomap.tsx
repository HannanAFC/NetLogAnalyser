// routes/_authenticated/geomap.tsx
import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';

import { CountrySidebarList } from '#/components/geomap/country-sidebar-list';
import { WorldChoropleth } from '#/components/geomap/world-choropleth';
import { TimeRangePicker } from '#/components/ui/time-range-picker';
import { Button } from '#/components/ui/button';
import { useGeo } from '#/features/analytics/hooks';
import { timeRangeSearchSchema } from '#/lib/time-range/schema';
import { createUseTimeRange, setCustomRange, setPreset } from '#/lib/time-range/use-time-range';
import type { Direction } from '#/features/analytics/schemas';

export const Route = createFileRoute( '/_authenticated/geomap' )( {
	validateSearch: timeRangeSearchSchema,
	component:      GeomapPage
} );

const useTimeRange = createUseTimeRange( '/_authenticated/geomap' );

function GeomapPage()
{
	const [ range, setRange, search ]  = useTimeRange();
	const [ direction, setDirection ]  = useState< Direction >( 'src' );

	const { data, isPending, isError } = useGeo( { ...range, direction, limit: 50 } );

	const resolvedRows   = ( data?.rows ?? [] ).filter( ( row ) => row.country_code !== null );
	const unresolvedRows = ( data?.rows ?? [] ).filter( ( row ) => row.country_code === null );

	return (
		<div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
			<div className="flex flex-wrap items-center gap-4">
				<TimeRangePicker
					search={ search }
					onPresetChange={ ( preset ) => setPreset( setRange, preset ) }
					onCustomRangeChange={ ( start, end ) => setCustomRange( setRange, start, end ) }
				/>
				<div role="group" aria-label="Direction" className="flex gap-1">
					<Button type="button" variant={ direction === 'src' ? 'primary' : 'ghost' } onClick={ () => setDirection( 'src' ) }>
						Source
					</Button>
					<Button type="button" variant={ direction === 'dst' ? 'primary' : 'ghost' } onClick={ () => setDirection( 'dst' ) }>
						Destination
					</Button>
				</div>
			</div>

			{ isPending && <div className="h-100 animate-pulse" aria-hidden="true" /> }
			{ isError && <p className="text-text-secondary text-sm">Couldn't load geo distribution.</p> }

			{ data && (
				<div className="grid gap-6 md:grid-cols-[2fr_1fr]">
					<WorldChoropleth rows={ resolvedRows } />
					<CountrySidebarList rows={ [ ...resolvedRows, ...unresolvedRows ] } isLoading={ isPending } isError={ isError } />
				</div>
			) }
		</div>
	);
}