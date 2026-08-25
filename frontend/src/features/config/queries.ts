import { queryOptions } from '@tanstack/react-query';
import { getConfig } from './api';

export const configQueryOptions = queryOptions(
{
	queryKey:  [ 'config' ],
	queryFn:   getConfig,
	staleTime: 5 * 60_000
} );