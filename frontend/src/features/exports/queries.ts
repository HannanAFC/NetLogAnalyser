import { getDataExportsRequest } from './api';
import { exportsQueryKey } from '#/lib/exports/query-key';
import { queryOptions } from '@tanstack/react-query';

export const exportsQueryOptions = queryOptions(
{
	queryKey: exportsQueryKey,
	queryFn: getDataExportsRequest
} );