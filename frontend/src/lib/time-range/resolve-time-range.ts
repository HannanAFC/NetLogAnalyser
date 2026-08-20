import type { TimeRangeParams } from '#/features/analytics/schemas';

import type { TimeRangePreset, TimeRangeSearch } from './schema';

const HOUR = 60 * 60 * 1000;
const DAY  = 24 * HOUR;

const PRESET_DURATION_MS: Record< Exclude< TimeRangePreset, 'custom' >, number > =
{
	'1h':  HOUR,
	'24h': DAY,
	'7d':  7 * DAY,
	'30d': 30 * DAY
};

// Same as backend to prevent an invalide range from being pickable from the frontend
const MAX_RANGE_MS = 30 * DAY;

export function resolveTimeRange( search: TimeRangeSearch ): TimeRangeParams
{
	const now = new Date( );

	if ( search.preset === 'custom' && search.start && search.end )
	{
		const start = new Date( search.start );
		const end   = new Date( search.end );

		if ( end.getTime( ) - start.getTime( ) > MAX_RANGE_MS )
		{
			return { start: new Date( end.getTime( ) - MAX_RANGE_MS ), end };
		}

		return { start, end };
	}

	const durationMs = PRESET_DURATION_MS[ search.preset === 'custom' ? '24h' : search.preset ];
	return { start: new Date( now.getTime( ) - durationMs ), end: now };
}