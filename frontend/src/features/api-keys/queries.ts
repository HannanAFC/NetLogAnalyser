import { getApiKeysRequest } from '#/features/api-keys/api';
import { apiKeysQueryKey } from '#/lib/api-keys/query-key';
import { queryOptions } from '@tanstack/react-query';

export const apiKeysQueryOptions = queryOptions(
{
	queryKey: apiKeysQueryKey,
	queryFn: getApiKeysRequest
} );