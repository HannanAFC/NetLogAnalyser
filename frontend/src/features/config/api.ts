import type { ConfigResponse } from '#/lib/config/types';
import { apiClient } from '#/lib/api/client';

export async function getConfig( ): Promise< ConfigResponse >
{
    const { data } = await apiClient.get< ConfigResponse >( '/config' );
    return data;
}