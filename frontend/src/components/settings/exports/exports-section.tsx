import { Button } from '#/components/ui/button';
import { BodySm } from '#/components/ui/heading';
import type { SkeletonColumn } from '#/components/ui/skeleton-table';
import { TableNoRecentsErrorMessage } from '#/components/ui/table-no-recents-error-message';
import { TanStackDataTable } from '#/components/ui/tanstack-data-table';
import { useCreateDataExport, useDataExports, useGetDataExportDownloadLink } from '#/features/exports/hooks';
import { apiError } from '#/lib/api/errors';
import type { DataExport, DataExportStatusEnum, DataExportTriggeredByEnum } from '#/lib/exports/types';
import { cn, formatApiKeyDate } from '#/lib/utils';
import type { SettingsSectionProps } from '#/routes/_authenticated/settings';
import { useForm } from '@tanstack/react-form';
import { createColumnHelper, metaHelper, tableFeatures, useTable } from '@tanstack/react-table';
import { DownloadIcon, Plus } from 'lucide-react';
import { useMemo } from 'react';

interface ExportsTableColumnMeta
{
	className?: string;
}

const features = tableFeatures(
{
	columnMeta: metaHelper< ExportsTableColumnMeta >( )
} );

const SKELETON_COLUMNS: SkeletonColumn[ ] =
[
    { skeletonWidth: 'w-42' },
    { skeletonWidth: 'w-16' },
    { skeletonWidth: 'w-17' },
    { skeletonWidth: 'w-16' },
    { skeletonWidth: 'w-42' },
    { skeletonWidth: 'w-42' },
    { skeletonWidth: 'w-42' },
    { skeletonWidth: 'w-10' }
];

const columnHelper = createColumnHelper< typeof features, DataExport >( );

const EMPTY_ROWS: DataExport[ ] = [ ];

const triggerMap: Record< DataExportTriggeredByEnum, string > =
{
    MANUAL:        'Manual',
    RETENTION_JOB: 'Automatic'
};

const statusMap: Record< DataExportStatusEnum, string > =
{
    PENDING: 'Pending',
    READY:   'Ready',
    FAILED:  'Failed'
};

export function ExportsSection( { className }: SettingsSectionProps )
{
    const columns = useMemo( ( ) =>
		columnHelper.columns(
		[
			columnHelper.accessor(
				'created_at',
				{
					header: 'Created at',
					meta:   { className: 'text-xs text-text-secondary' },
					cell:   ( info ) => formatApiKeyDate( info.getValue( ) )
				}
			),
            columnHelper.accessor(
				'status',
				{
					header: 'Type',
					cell:   ( info ) => statusMap[ info.getValue( ) ]
				}
			),
			columnHelper.accessor(
				'triggered_by',
				{
					header: 'Type',
					cell:   ( info ) => triggerMap[ info.getValue( ) ]
				}
			),
            columnHelper.accessor(
				'file_size_bytes',
				{
					header: 'Size',
					meta:   { className: 'text-text-secondary tabular-nums' },
					cell:   ( info ) =>
                    {
                        if ( info.row.original.file_size_bytes !== null )
                        {
                            return ( info.row.original.file_size_bytes / 1000000 ).toFixed( 2 ) + ' MB';
                        }
                        else
                        {
                            return '-';
                        }
                    }
				}
			),
            columnHelper.accessor(
				'expires_at',
				{
					header: 'Expires at',
					meta:   { className: 'text-xs text-text-secondary' },
					cell:   ( info ) => formatApiKeyDate( info.getValue( ) )
				}
			),
            columnHelper.accessor(
				'purged_at',
				{
					header: 'Purged at',
					meta:   { className: 'text-xs text-text-secondary' },
					cell:   ( info ) => formatApiKeyDate( info.getValue( ) )
				}
			),
            columnHelper.accessor(
				'last_downloaded_at',
				{
					header: 'Last download',
					meta:   { className: 'text-xs text-text-secondary' },
					cell:   ( info ) => formatApiKeyDate( info.getValue( ) )
				}
			),
            columnHelper.display(
            {
                id:     'download',
                header: 'Download',
                meta:   { className: 'flex justify-center' },
                cell:   ( { row } ) =>
                {
                    if ( row.original.purged_at === null )
                    {
                        return (
                            <button
                                type="button"
                                className="cursor-pointer text-text-secondary hover:text-text-primary transition-colors flex"
                                onClick={ ( ) => handleDownloadExport( row.original.id ) }
                            >
                                <DownloadIcon size={ 18 } />
                            </button>
                        );
                    }
                    else
                    {
                        return (
                            <>N/A</>
                        );
                    }
                }
            } )
		] ),
		[ ]
	);

    const { data, isLoading, isError } = useDataExports( );
    const createDataExport             = useCreateDataExport( );
    const getDataExportDownloadLink    = useGetDataExportDownloadLink( );

    const table = useTable(
	{
		key:      'exports-table',
		features: features,
		columns:  columns,
		data:     data?.rows ?? EMPTY_ROWS,
		getRowId: ( row ) => row.id
	} );

    const createExportForm = useForm(
    {
        onSubmit: async( ) =>
        {
            await createDataExport.mutateAsync( );
            createExportForm.reset( );
        }
    } );


    async function handleDownloadExport( id: string )
    {
        const result = await getDataExportDownloadLink.mutateAsync( id );
        if ( result.download_url )
        {
            window.open( result.download_url, '_blank' );
        }
    }

    return (
        <div className= { cn( 'space-y-6', className ) }>
            <div className='flex flex-row justify-between items-center gap-4'>
                <BodySm className="mb-2 font-semibold uppercase tracking-[0.08em] text-text-tertiary">
                    Exports
                </BodySm>
                <form
                    onSubmit={ ( e ) =>
                    {
                        e.preventDefault( );
                        e.stopPropagation( );
                        createExportForm.handleSubmit( );
                    } }
                >
                    <createExportForm.Subscribe>
                        { ( ) => (
                            <Button
                                type="submit"
                                disabled={ createDataExport.isPending }
                                className="disabled:opacity-50"
                                variant='primary'
                            >
                                <Plus className="h-3.5 w-3.5" />
                                { createDataExport.isPending ? 'Starting…' : 'Start export' }
                            </Button>
                        ) }
                    </createExportForm.Subscribe>
                </form>
            </div>
            { createDataExport.isError && (
                <BodySm className="text-critical">
                    { apiError( createDataExport.error ) ?? 'Failed to start export.' }
                </BodySm>
            ) }
            <TanStackDataTable
                table={ table }
                skeletonColumns={ SKELETON_COLUMNS }
                isLoading={ isLoading }
                isError={ isError }
                emptyMessage={
                    <TableNoRecentsErrorMessage>
                        You have not exported any data yet. Start an export above!
                    </TableNoRecentsErrorMessage>
                }
                errorMessage={
                    <TableNoRecentsErrorMessage>
                        An error occurred whilst loading your exports, please try again.
                    </TableNoRecentsErrorMessage>
                }
                maxHeight='sm'
                virtualize={ false }
            />
        </div>
    );
}