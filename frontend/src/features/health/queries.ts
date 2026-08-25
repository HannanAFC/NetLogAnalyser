import { queryOptions } from '@tanstack/react-query';
import { getHealth } from './api';

export const healthQueryOptions = queryOptions(
{
	queryKey:  [ 'health' ],
	queryFn:   getHealth,
	staleTime: 5 * 60_000
} );