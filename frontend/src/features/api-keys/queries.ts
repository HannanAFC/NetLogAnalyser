import { queryOptions } from '@tanstack/react-query';
import { getApiKeysRequest } from '#/features/api-keys/api';
import { apiKeysQueryKey } from '#/lib/api-keys/query-key';

export const apiKeysQueryOptions = queryOptions(
{
	queryKey: apiKeysQueryKey,
	queryFn: getApiKeysRequest
} );