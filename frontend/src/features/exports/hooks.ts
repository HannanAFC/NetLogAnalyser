import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { exportsQueryOptions } from './queries';
import { createDataExportRequest, getDataExportDownloadLinkRequest } from './api';
import { exportsQueryKey } from '#/lib/exports/query-key';

export function useDataExports( )
{
    return useQuery( exportsQueryOptions );
}

export function useCreateDataExport( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( ) => createDataExportRequest( ),
        onSuccess: ( ) =>
        {
            queryClient.invalidateQueries( { queryKey: exportsQueryKey } );
        }
    } );
}

export function useGetDataExportDownloadLink( )
{
    return useMutation(
    {
        mutationFn: ( exportId: string ) => getDataExportDownloadLinkRequest( exportId )
    } );
}