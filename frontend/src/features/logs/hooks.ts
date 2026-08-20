import { useInfiniteQuery, useQuery } from '@tanstack/react-query';

import {
	DEFAULT_HISTORY_PAGE_LIMIT,
	DEFAULT_INITIAL_LOGS_LIMIT,
	initialLogsQueryOptions,
	logsInfiniteQueryOptions
} from '#/features/logs/queries';
import type { LogEntry } from '#/lib/logs/types';

export function useInitialLogs( limit: number = DEFAULT_INITIAL_LOGS_LIMIT )
{
	const query = useQuery( initialLogsQueryOptions( limit ) );

	const entries: LogEntry[ ] = query.data?.entries ?? [ ];

	return {
		entries:   entries,
		isLoading: query.isLoading,
		isError:   query.isError
	};
}

export function useLogHistory( limit: number = DEFAULT_HISTORY_PAGE_LIMIT )
{
	const query = useInfiniteQuery( logsInfiniteQueryOptions( limit ) );

	const entries: LogEntry[ ] = query.data?.pages.flatMap( ( page ) => page.entries ) ?? [ ];

	return {
		entries:            entries,
		isLoading:          query.isLoading,
		isError:            query.isError,
		hasNextPage:        query.hasNextPage,
		isFetchingNextPage: query.isFetchingNextPage,
		fetchNextPage:      query.fetchNextPage
	};
}