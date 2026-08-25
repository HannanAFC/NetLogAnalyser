import { apiClient } from '#/lib/api/client';
import type { HealthResponse } from '#/lib/health/types';

export async function getHealth( ): Promise< HealthResponse >
{
	const { data } = await apiClient.get< HealthResponse >( '/health' );
	return data;
}