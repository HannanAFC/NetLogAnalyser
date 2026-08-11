import type { LogEntry } from '#/lib/logs/types';
import { LogEntryRow } from './log-entry-row';
import { getLogEntryKey } from '#/lib/logs/entry-key';
import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '#/lib/utils';
import { DataTable } from '#/components/ui/data-table';
import type { TableHeightVariant } from '#/components/ui/data-table';
import type { SkeletonColumn } from '#/components/ui/skeleton-table';

const LOG_COLUMNS: SkeletonColumn[ ] =
[
	{ header: 'Time' },
	{ header: 'Source' },
	{ header: '' },
	{ header: 'Destination' },
	{ header: 'Protocol' },
	{ header: 'Size',       headerClassName: 'text-right' },
	{ header: 'Source country' },
	{ header: 'Destination country' },
	{ header: 'Anomaly' }
];

interface LogTableProps extends HTMLAttributes< HTMLDivElement >
{
	isLoading:                boolean;
	isError:                  boolean;
	loadingErrorMessage:      ReactNode;
	noRecentLogsErrorMessage: ReactNode;
	entries:                  LogEntry[ ];
	maxHeight?:               TableHeightVariant;
}

export function LogTable(
{
	className,
	isLoading,
	isError,
	loadingErrorMessage,
	noRecentLogsErrorMessage,
	entries,
	maxHeight = 'md'
}: LogTableProps )
{
	return (
		<DataTable< LogEntry >
			className={ cn( 'mt-8', className ) }
			columns={ LOG_COLUMNS }
			data={ entries }
			renderRow={ ( entry, index ) => <LogEntryRow entry={ entry } dataIndex={ index } key={ getLogEntryKey( entry ) } /> }
			getRowKey={ ( entry ) => getLogEntryKey( entry ) }
			isLoading={ isLoading }
			isError={ isError }
			errorMessage={ loadingErrorMessage }
			emptyMessage={ noRecentLogsErrorMessage }
			maxHeight={ maxHeight }
			virtualize={ true }
		/>
	);
}
