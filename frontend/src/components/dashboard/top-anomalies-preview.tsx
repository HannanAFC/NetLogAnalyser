import { useAnomalies } from '#/features/analytics/hooks';
import type { TimeRangeParams } from '#/features/analytics/schemas';
import type { HTMLAttributes } from 'react';
import type { LogEntry } from '#/lib/logs/types';
import type { SkeletonColumn } from '../ui/skeleton-table';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';
import { TanStackDataTable } from '../ui/tanstack-data-table';
import {
	tableFeatures,
	useTable,
	createColumnHelper,
    metaHelper
} from '@tanstack/react-table';
import { useMemo } from 'react';
import { AnomalyIndicator } from '../live-feed/anomaly-indicator';

const PREVIEW_MIN_SCORE = 0.8;
const PREVIEW_LIMIT     = 5;

interface TopAnomaliesPreviewProps extends HTMLAttributes< HTMLDivElement >
{
	range: TimeRangeParams;
}

interface TopAnomaliesPreviewColumnMeta
{
    className?: string
}

const SKELETON_COLUMNS: SkeletonColumn[ ] =
[
    { },
    { },
    { },
    { }
];

const features = tableFeatures(
{
    columnMeta: metaHelper< TopAnomaliesPreviewColumnMeta >( )
} );

const columnHelper = createColumnHelper< typeof features, LogEntry >( );

export function TopAnomaliesPreview( { range }: TopAnomaliesPreviewProps )
{
    const columns = useMemo( ( ) =>
        columnHelper.columns(
        [
            columnHelper.accessor(
                'src_ip',
                {
                    header: 'Source',
                    meta:   { className: 'font-mono text-sm' },
                    cell:   ( info ) => `${ info.getValue( ) }:${ info.row.original.src_port }`
                }
            ),
            columnHelper.display(
				{
					id:     'arrow',
					header: '',
                    meta:   { className: 'text-text-secondary' },
					cell:   ( ) => <span className="text-text-secondary">→</span>
				}
            ),
            columnHelper.accessor(
                'dst_ip',
                {
                    header: 'Destination',
                    meta:   { className: 'font-mono text-sm' },
                    cell:   ( info ) => `${ info.getValue( ) }:${ info.row.original.dst_port }`
                }
            ),
            columnHelper.accessor(
                'anomaly_score',
                {
                    header: 'Anomaly score',
                    cell:   ( info ) => <AnomalyIndicator score={ info.getValue( ) } reasons={ info.row.original.anomaly_reasons } />
                }
            )
        ] ),
        [ ]
    );

	const { pages, isError, isLoading } = useAnomalies( { ...range, min_score: PREVIEW_MIN_SCORE, limit: PREVIEW_LIMIT } );
	const rows = pages[ 0 ]?.rows ?? [ ];

    const table = useTable(
    {
        key:                'top-anomalies-table',
        features:           features,
        columns:            columns,
        data:               rows
    } );

	return (
        <TanStackDataTable
            table={ table }
            skeletonColumns={ SKELETON_COLUMNS }
            isLoading={ isLoading }
            isError={ isError }
            errorMessage={ <TableLoadingErrorMessage>An error occurred whilst loading anomalies, please try again.</TableLoadingErrorMessage> }
            emptyMessage={ <TableNoRecentsErrorMessage>No anomalies detected in the current time range.</TableNoRecentsErrorMessage> }
            maxHeight='sm'
            virtualize={ false }
        />
	);
}