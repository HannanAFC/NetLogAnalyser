import { apiClient } from '#/lib/api/client';
import type { ConfigResponse } from '#/lib/config/types';

export async function getConfig( ): Promise< ConfigResponse >
{
    const { data } = await apiClient.get< ConfigResponse >( '/config' );
    return data;
}