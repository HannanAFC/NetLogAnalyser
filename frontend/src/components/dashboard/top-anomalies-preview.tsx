import { useAnomalies } from '#/features/analytics/hooks';
import type { TimeRangeParams } from '#/features/analytics/schemas';
import type { HTMLAttributes } from 'react';
import { DataTable } from '../ui/data-table';
import type { LogEntry } from '#/lib/logs/types';
import { getLogEntryKey } from '#/lib/logs/entry-key';
import type { SkeletonColumn } from '../ui/skeleton-table';
import { TopAnomaliesRow } from './top-anomalies-row';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';

const PREVIEW_MIN_SCORE = 0.8;
const PREVIEW_LIMIT     = 5;

interface TopAnomaliesPreviewProps extends HTMLAttributes< HTMLDivElement >
{
	range: TimeRangeParams;
}

const LOG_COLUMNS: SkeletonColumn[ ] =
[
    { header: 'Source' },
    { header: '' },
    { header: 'Destination' },
    { header: 'Anomaly score' }
];

export function TopAnomaliesPreview( { className, range }: TopAnomaliesPreviewProps )
{
	const { data, isError, isLoading } = useAnomalies( { ...range, min_score: PREVIEW_MIN_SCORE, limit: PREVIEW_LIMIT } );
	const rows = data?.pages[ 0 ]?.rows ?? [];

	return (
        <DataTable< LogEntry >
            className={ className }
            columns={ LOG_COLUMNS }
            data={ rows }
            renderRow={ ( entry ) => <TopAnomaliesRow key={ getLogEntryKey( entry ) } row={ entry } /> }
            getRowKey={ ( entry ) => getLogEntryKey( entry ) }
            isLoading={ isLoading }
            isError={ isError }
            errorMessage={ <TableLoadingErrorMessage>An error occurred whilst loading anomalies, please try again.</TableLoadingErrorMessage> }
            emptyMessage={ <TableNoRecentsErrorMessage>No anomalies detected in the current time range.</TableNoRecentsErrorMessage> }
            maxHeight='sm'
            virtualize={ false }
        />
	);
}