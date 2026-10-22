import { queryOptions } from '@tanstack/react-query';
import { getDataExportsRequest } from './api';
import { exportsQueryKey } from '#/lib/exports/query-key';

export const exportsQueryOptions = queryOptions(
{
	queryKey: exportsQueryKey,
	queryFn: getDataExportsRequest
} );