import { useAnomalies } from '#/features/analytics/hooks';
import type { AnomaliesFilterParams } from '#/features/analytics/schemas';
import {
	tableFeatures,
	useTable,
	createColumnHelper,
	rowPaginationFeature,
	rowExpandingFeature,
	createExpandedRowModel,
	metaHelper
} from '@tanstack/react-table';
import type { PaginationState } from '@tanstack/react-table';
import type { LogEntry } from '#/lib/logs/types';
import { Fragment, useEffect, useMemo, useState } from 'react';
import { Button } from '#/components/ui/button';
import { ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
import { formatApiKeyDate } from '#/lib/utils';
import { AnomalyIndicator } from '../live-feed/anomaly-indicator';
import { TanStackDataTable } from '../ui/tanstack-data-table';
import type { SkeletonColumn } from '../ui/skeleton-table';

interface AnomaliesTableProps
{
	filter: AnomaliesFilterParams;
}

interface AnomaliesTableColumnMeta
{
	className?: string;
}

const features = tableFeatures(
{
	rowPaginationFeature: rowPaginationFeature,
	rowExpandingFeature:  rowExpandingFeature,
	expandedRowModel:     createExpandedRowModel( ),
	columnMeta:           metaHelper< AnomaliesTableColumnMeta >( )
} );

const SKELETON_COLUMNS: SkeletonColumn[ ] =
[
	{ skeletonWidth: 'w-0' },
	{ skeletonWidth: 'w-20' },
	{ skeletonWidth: 'w-40' },
	{ skeletonWidth: 'w-0' },
	{ skeletonWidth: 'w-40' },
	{ skeletonWidth: 'w-20' },
	{ skeletonWidth: 'w-35' }
];

const columnHelper = createColumnHelper< typeof features, LogEntry >( );

const EMPTY_ROWS: LogEntry[ ] = [ ];

export function AnomaliesTable( { filter }: AnomaliesTableProps )
{
	const columns = useMemo( ( ) =>
		columnHelper.columns(
		[
			columnHelper.display(
				{
					id:     'expand',
					header: '',
					cell:   ( { row } ) =>
						row.getCanExpand( ) ? (
							<button
								type="button"
								className="cursor-pointer text-text-secondary hover:text-text-primary transition-colors flex"
								onClick={ row.getToggleExpandedHandler( ) }
								aria-label={ row.getIsExpanded( ) ? 'Collapse row' : 'Expand row' }
							>
								<ChevronDown
									className={ `h-5 w-5 transition-transform duration-150 ${ row.getIsExpanded( ) ? '' : '-rotate-90' }` }
								/>
							</button>
						) : null
				} ),
			columnHelper.accessor(
				'captured_at',
				{
					header: 'Time',
					meta:   { className: 'text-xs text-text-secondary' },
					cell:   ( info ) => formatApiKeyDate( info.getValue( ) )
				}
			),
			columnHelper.accessor(
				'src_ip',
				{
					header: 'Source IP',
					meta:   { className: 'font-mono text-sm' },
					cell:   ( info ) =>
					{
						const srcPort = info.row.original.src_port;
						return `${ info.getValue( ) }:${ srcPort }`;
					}
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
					cell:   ( info ) =>
					{
						const dstPort = info.row.original.dst_port;
						return `${ info.getValue( ) }:${ dstPort }`;
					}
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
				'anomaly_score',
				{
					header: 'Score',
					cell:   ( info ) =>
					(
						<AnomalyIndicator
							score={ info.getValue( ) }
							reasons={ info.row.original.anomaly_reasons }
						/>
					)
				}
			)
		] ),
		[ ]
	);

	const { pages, isLoading, isError, isFetchingNextPage, fetchNextPage } = useAnomalies( filter );

	const [ pagination, setPagination ] = useState< PaginationState >(
	{
		pageIndex: 0,
		pageSize:  filter.limit
	} );

	// Reset to first page whenever the filter changes.
	useEffect( ( ) =>
	{
		setPagination( ( prev ) =>
			prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }
		);
	}, [ filter ] );

	const currentPage = pages[ pagination.pageIndex ];
	const hasCachedNextPage = Boolean( pages[ pagination.pageIndex + 1 ] );
	const canNextPage = hasCachedNextPage || Boolean( currentPage?.has_more );
	const canPreviousPage = pagination.pageIndex > 0;

	const table = useTable(
	{
		key:                'anomalies-table',
		features:           features,
		columns:            columns,
		data:               currentPage?.rows ?? EMPTY_ROWS,
		pageCount:          -1,
		manualPagination:   true,
		state:              { pagination },
		onPaginationChange: setPagination,
		getRowCanExpand:    ( row ) => row.original.anomaly_reasons.length > 0
	} );

	async function goToNextPage( )
	{
		const nextPageIndex = pagination.pageIndex + 1;

		if ( !pages[ nextPageIndex ] )
		{
			const result = await fetchNextPage( );
			if ( !result.data?.pages[ nextPageIndex ] ) return;
		}

		table.nextPage( );
	}

	return (
		<div>
			<TanStackDataTable
				table={ table }
				skeletonColumns={ SKELETON_COLUMNS }
				isLoading={ isLoading }
				isError={ isError }
				errorMessage={ <p className="text-text-secondary text-sm">Couldn't load anomalies.</p> }
				emptyMessage={ <p className="text-text-secondary text-sm">No anomalies found.</p> }
				isRowExpanded={ ( row ) => row.getIsExpanded( ) }
				renderExpandedRow={ ( row ) => (
					<div className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
						{ row.original.anomaly_reasons.map( ( reason, idx ) => (
							<Fragment key={ idx }>
								<span className="text-xs font-mono tabular-nums text-text-secondary">
									{ reason.score.toFixed( 2 ) }
								</span>
								<span className="text-xs text-text-primary">
									<strong>{ reason.name }</strong>
									{ reason.detail && <span className="text-text-secondary"> - { reason.detail }</span> }
								</span>
							</Fragment>
						) ) }
					</div>
				) }
				virtualize={ true }
			/>

			<div className="flex items-center justify-between mt-3 text-sm text-text-secondary">
				<span>
					Page { pagination.pageIndex + 1 }
					{ isFetchingNextPage && ' (loading…)' }
				</span>
				<div className="flex items-center gap-2">
					<Button
						variant="secondary"
						size="sm"
						onClick={ ( ) => table.previousPage( ) }
						disabled={ !canPreviousPage || isFetchingNextPage }
						aria-label="Previous page"
					>
						<ChevronLeft className="h-4 w-4" />
						Prev
					</Button>
					<Button
						variant="secondary"
						size="sm"
						onClick={ goToNextPage }
						disabled={ !canNextPage || isFetchingNextPage }
						aria-label="Next page"
					>
						Next
						<ChevronRight className="h-4 w-4" />
					</Button>
				</div>
			</div>
		</div>
	);
}