import { apiClient } from '#/lib/api/client';
import type { GetLogsResponse } from '#/lib/logs/types';

export interface GetLogsParams
{
	cursor?: string
	limit?:  number
}

export async function getLogsRequest( params: GetLogsParams = { } ): Promise< GetLogsResponse >
{
	const { data } = await apiClient.get< GetLogsResponse >( '/logs', { params } );
	return data;
}