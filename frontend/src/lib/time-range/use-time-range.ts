import { getRouteApi } from '@tanstack/react-router';
import { useMemo } from 'react';

import type { TimeRangeParams } from '#/features/analytics/schemas';

import { resolveTimeRange } from './resolve-time-range';
import type { TimeRangeSearch } from './schema';

type SetTimeRange = ( next: Partial< TimeRangeSearch > ) => void;

export function createUseTimeRange( routeId: string )
{
	const routeApi = getRouteApi( routeId );

	return function useTimeRange( ): [ TimeRangeParams, SetTimeRange, TimeRangeSearch ]
	{
		const search: TimeRangeSearch = routeApi.useSearch( );
		const navigate                = routeApi.useNavigate( );

		const range = useMemo( ( ) => resolveTimeRange( search ), [ search ] );

		function setRange( next: Partial< TimeRangeSearch > )
		{
			navigate( { search: ( prev: TimeRangeSearch ) => ( { ...prev, ...next } ), replace: true } );
		}

		return [ range, setRange, search ];
	};
}

export function setCustomRange( setRange: SetTimeRange, start: Date, end: Date )
{
	setRange( { preset: 'custom', start: start.toISOString( ), end: end.toISOString( ) } );
}