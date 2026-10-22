import type { CreateDataExportResponse, GetDataExportDownloadLinkResponse, GetDataExportsResponse } from '#/lib/exports/types';
import { apiClient } from '#/lib/api/client';

export async function getDataExportsRequest( ): Promise< GetDataExportsResponse >
{
    const { data } = await apiClient.get< GetDataExportsResponse >( '/exports' );
    return data;
}

export async function createDataExportRequest( ): Promise< CreateDataExportResponse >
{
    const { data } = await apiClient.post< CreateDataExportResponse >( '/exports' );
    return data;
}

export async function getDataExportDownloadLinkRequest( exportId: string ): Promise< GetDataExportDownloadLinkResponse >
{
    const { data } = await apiClient.post< GetDataExportDownloadLinkResponse >( `/exports/${ exportId }/download-link` );
    return data;
}