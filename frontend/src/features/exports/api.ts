import { apiClient } from '#/lib/api/client';
import type { CreateDataExportResponse, GetDataExportsResponse, GetDataExportDownloadLinkResponse } from '#/lib/exports/types';

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