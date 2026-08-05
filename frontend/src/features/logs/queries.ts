import { infiniteQueryOptions, queryOptions } from '@tanstack/react-query';

import { getLogsRequest } from '#/features/logs/api';
import { logsQueryKey } from '#/lib/logs/query-key';
import type { GetLogsResponse } from '#/lib/logs/types';

export const DEFAULT_INITIAL_LOGS_LIMIT = 20;
export const DEFAULT_HISTORY_PAGE_LIMIT = 25;

/**
 * Query options for the live feed initial logs. For general log history use `logsInfiniteQueryOptions`,
 * which includes pagination. Doesn't include refetching.
 */
export function initialLogsQueryOptions( limit: number = DEFAULT_INITIAL_LOGS_LIMIT )
{
	return queryOptions(
    {
		queryKey: [ ...logsQueryKey( limit ), 'initial' ] as const,
		queryFn:  ( ) => getLogsRequest( { limit } ),
		staleTime: Infinity,
		retry:     false
	} );
}

/**
 * Query options for general purpose log history, includes pagination and refetching.
 */
export function logsInfiniteQueryOptions( limit: number = DEFAULT_HISTORY_PAGE_LIMIT )
{
	return infiniteQueryOptions(
    {
		queryKey:         logsQueryKey( limit ),
		queryFn:          ( { pageParam } ) => getLogsRequest( { cursor: pageParam, limit: limit } ),
		initialPageParam: undefined as string | undefined,
		getNextPageParam: ( lastPage: GetLogsResponse ) => lastPage.has_more ? ( lastPage.next_cursor ?? undefined ) : undefined
	} );
}