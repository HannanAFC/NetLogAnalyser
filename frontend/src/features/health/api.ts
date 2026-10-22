import type { HealthResponse } from '#/lib/health/types';
import { apiClient } from '#/lib/api/client';

export async function getHealth( ): Promise< HealthResponse >
{
	const { data } = await apiClient.get< HealthResponse >( '/health' );
	return data;
}