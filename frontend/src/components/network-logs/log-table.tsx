import type { LogEntry } from '#/lib/logs/types';
import { getLogEntryKey } from '#/lib/logs/entry-key';
import type { HTMLAttributes, ReactNode } from 'react';
import { formatRelativeTime } from '#/lib/utils';
import type { SkeletonColumn } from '#/components/ui/skeleton-table';
import { createColumnHelper, metaHelper, tableFeatures, useTable } from '@tanstack/react-table';
import { useMemo } from 'react';
import { AnomalyIndicator } from '../live-feed/anomaly-indicator';
import { TanStackDataTable } from '../ui/tanstack-data-table';
import type { TableHeightVariant } from '../ui/table-frame';

const SKELETON_COLUMNS: SkeletonColumn[ ] =
[
	{ },
	{ },
	{ },
	{ },
	{ },
	{ },
	{ },
	{ },
	{ }
];

interface LogTableColumnMeta
{
	className?: string;
}

const features = tableFeatures(
{
	columnMeta: metaHelper< LogTableColumnMeta >( )
} );

const columnHelper = createColumnHelper< typeof features, LogEntry >( );

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
	const columns = useMemo( ( ) =>
		columnHelper.columns(
		[
			columnHelper.accessor(
				'captured_at',
				{
					header: 'Time',
					meta:   { className: 'text-xs text-text-secondary' },
					cell:   ( info ) => formatRelativeTime( info.getValue( ) )
				}
			),
			columnHelper.accessor(
				'src_ip',
				{
					header: 'Source IP',
					meta:   { className: 'font-mono text-sm' },
					cell:   ( info ) => `${ info.getValue( ) }:${ info.row.original.src_port }`
				}
			),
			columnHelper.display(
				{
					id:     'arrow',
					header: '',
					meta:   { className: 'text-text-secondary' },
					cell:   ( ) => '→'
				}
			),
			columnHelper.accessor(
				'dst_ip',
				{
					header: 'Destination IP',
					meta:   { className: 'font-mono text-sm' },
					cell:   ( info ) => `${ info.getValue( ) }:${ info.row.original.dst_port }`
				}
			),
			columnHelper.accessor(
				'protocol',
				{
					header: 'Protocol',
					cell:   ( info ) => info.getValue( )
				}
			),
			columnHelper.accessor(
				'packet_size_bytes',
				{
					header: 'Packet size',
					meta:   { className: 'text-text-secondary tabular-nums' },
					cell:   ( info ) => info.getValue( ) + ' B'
				}
			),
			columnHelper.accessor(
				'src_country_code',
				{
					header: 'Source country',
					cell:   ( info ) => info.row.original.src_geo_status === 'resolved' ?  info.row.original.src_country_code :  info.row.original.src_geo_status.toUpperCase( )
				}
			),
			columnHelper.accessor(
				'dst_country_code',
				{
					header: 'Destination country',
					cell:   ( info ) => info.row.original.dst_geo_status === 'resolved' ?  info.row.original.dst_country_code :  info.row.original.dst_geo_status.toUpperCase( )
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

	const table = useTable(
	{
		key:      'anomalies-table',
		features: features,
		columns:  columns,
		data:     entries,
		getRowId: ( row ) => getLogEntryKey( row )
	} );

	return (
		<TanStackDataTable
			table={ table }
			skeletonColumns={ SKELETON_COLUMNS }
			isLoading={ isLoading }
			isError={ isError }
			errorMessage={ loadingErrorMessage }
			emptyMessage={ noRecentLogsErrorMessage }
			maxHeight={ maxHeight }
			virtualize={ true }
			className={ className }
		/>
	);
}
