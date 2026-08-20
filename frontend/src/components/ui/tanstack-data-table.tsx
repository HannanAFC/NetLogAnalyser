import { Fragment, useRef } from 'react';
import type { ReactNode } from 'react';
import type { Row, Table } from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { TableFrame } from './table-frame';
import type { TableHeightVariant } from './table-frame';
import { SkeletonTableRows } from './skeleton-table';
import type { SkeletonColumn } from './skeleton-table';
import { cn } from '#/lib/utils';

const DEFAULT_ESTIMATED_ROW_HEIGHT = 40;

interface TanStackDataTableProps< TFeatures, TData >
{
	table:                 Table< TFeatures, TData >;
	skeletonColumns:       SkeletonColumn[ ];
	isLoading?:            boolean;
	isError?:              boolean;
	errorMessage?:         ReactNode;
	emptyMessage?:         ReactNode;
	maxHeight?:            TableHeightVariant;
	maxHeightPx?:          number;
	overlaySkeletonCount?: number;
	className?:            string;
	virtualize?:           boolean;
	estimatedRowHeight?:   number;
	isRowExpanded?:        ( row: Row< TFeatures, TData > ) => boolean;
	renderExpandedRow?:    ( row: Row< TFeatures, TData > ) => ReactNode;
}

const TableHeightPx: Record< TableHeightVariant, number > = { sm: 400, md: 800, lg: 1200 };

export function TanStackDataTable< TFeatures, TData >(
{
	table,
	skeletonColumns,
	isLoading = false,
	isError = false,
	errorMessage,
	emptyMessage,
	maxHeight = 'md',
	maxHeightPx,
	overlaySkeletonCount = 10,
	className,
	virtualize = false,
	estimatedRowHeight = DEFAULT_ESTIMATED_ROW_HEIGHT,
	isRowExpanded,
	renderExpandedRow
}: TanStackDataTableProps< TFeatures, TData > )
{
	const scrollRef = useRef< HTMLDivElement >( null );
	const rows = table.getRowModel( ).rows;
	const isEmpty = !isLoading && !isError && rows.length === 0;
	const dynamicHeight = Boolean( renderExpandedRow );
	const resolvedMaxHeightPx = maxHeightPx ?? TableHeightPx[ maxHeight ];

	return (
		<TableFrame
			className={ className }
			scrollRef={ scrollRef }
			isEmpty={ isEmpty }
			isError={ isError }
			errorMessage={ errorMessage }
			emptyMessage={ emptyMessage }
			maxHeight={ maxHeight }
		>
			<table className="w-full text-left tabular-nums">
				<thead>
					{ table.getHeaderGroups( ).map( ( headerGroup ) => (
						<tr
							key={ headerGroup.id }
							className="border-b border-border bg-surface-card text-xs text-nowrap font-medium text-text-secondary"
						>
							{ headerGroup.headers.map( ( header ) => (
								<th
									key={ header.id }
									className={ cn( 'px-3 py-2 font-medium', header.column.columnDef.meta?.headerClassName ) }
								>
									{ header.isPlaceholder ? null : <table.FlexRender header={ header } /> }
								</th>
							) ) }
						</tr>
					) ) }
				</thead>

				{ isLoading && <SkeletonTableRows columns={ skeletonColumns } count={ overlaySkeletonCount } /> }

				{ !isLoading && !isError && rows.length > 0 ? (
					virtualize ? (
						<VirtualisedTanStackRows
							rows={ rows }
							getScrollElement={ ( ) => scrollRef.current }
							estimatedRowHeight={ estimatedRowHeight }
							columnCount={ table.getAllLeafColumns( ).length }
							maxHeightPx={ resolvedMaxHeightPx }
							dynamicHeight={ dynamicHeight }
							renderRowPair={ ( row ) => (
								<TableRowPair
									table={ table }
									row={ row }
									isExpanded={ isRowExpanded?.( row ) ?? false }
									renderExpandedRow={ renderExpandedRow }
								/>
							) }
						/>
					) : (
						<tbody>
							{ rows.map( ( row ) => (
								<TableRowPair
									key={ row.id }
									table={ table }
									row={ row }
									isExpanded={ isRowExpanded?.( row ) ?? false }
									renderExpandedRow={ renderExpandedRow }
								/>
							) ) }
						</tbody>
					)
				) : (
					<SkeletonTableRows columns={ skeletonColumns } count={ overlaySkeletonCount } />
				) }
			</table>
		</TableFrame>
	);
}

function TableRowPair< TFeatures, TData >(
{
	table,
	row,
	isExpanded,
	renderExpandedRow,
	rowRef
}:
{
	table:              Table< TFeatures, TData >;
	row:                Row< TFeatures, TData >;
	isExpanded:         boolean;
	renderExpandedRow?: ( row: Row< TFeatures, TData > ) => ReactNode;
	rowRef?:            ( el: HTMLTableRowElement | null ) => void;
} )
{
	return (
		<Fragment>
			<tr
				ref={ rowRef }
				data-index={ row.index }
				className="border-b border-border last:border-0 hover:bg-inset transition-colors duration-150"
			>
				{ row.getAllCells( ).map( ( cell ) => (
					<td
						key={ cell.id }
						className={ cn( 'whitespace-nowrap px-3 py-2 text-sm', cell.column.columnDef.meta?.className ) }
					>
						<table.FlexRender cell={ cell } />
					</td>
				) ) }
			</tr>
			{ renderExpandedRow && isExpanded && (
				<tr data-virtual-sibling className="border-b border-border last:border-0 bg-surface-card">
					<td colSpan={ row.getAllCells( ).length } className="px-3 py-3">
						{ renderExpandedRow( row ) }
					</td>
				</tr>
			) }
		</Fragment>
	);
}

interface VirtualisedTanStackRowsProps< TFeatures, TData >
{
	rows:                Row< TFeatures, TData >[ ];
	getScrollElement:    ( ) => HTMLElement | null;
	estimatedRowHeight:  number;
	columnCount:         number;
	maxHeightPx:         number;
	dynamicHeight:       boolean;
	renderRowPair:       ( row: Row< TFeatures, TData > ) => ReactNode;
}

function VirtualisedTanStackRows< TFeatures, TData >(
{
	rows,
	getScrollElement,
	estimatedRowHeight,
	columnCount,
	maxHeightPx,
	dynamicHeight,
	renderRowPair
}: VirtualisedTanStackRowsProps< TFeatures, TData > )
{
	const virtualizer = useVirtualizer(
	{
		count:            rows.length,
		getScrollElement: getScrollElement,
		estimateSize:     ( ) => estimatedRowHeight,
		overscan:         10,
		getItemKey:       ( index ) => rows[ index ].id,
		initialRect:      { width: 0, height: maxHeightPx },
		...( dynamicHeight && {
			measureElement: ( el: Element ) =>
			{
				const ownHeight = el.getBoundingClientRect( ).height;
				const sibling = el.nextElementSibling as HTMLElement | null;
				const siblingHeight = sibling?.dataset.virtualSibling !== undefined
					? sibling.getBoundingClientRect( ).height
					: 0;
				return ownHeight + siblingHeight;
			}
		} )
	} );

	const virtualItems = virtualizer.getVirtualItems( );
	const paddingTop = virtualItems.length > 0 ? virtualItems[ 0 ].start : 0;
	const paddingBottom = virtualItems.length > 0
		? virtualizer.getTotalSize( ) - virtualItems[ virtualItems.length - 1 ].end
		: 0;

	return (
		<tbody>
			{ paddingTop > 0 && (
				<tr aria-hidden style={ { height: paddingTop } }><td colSpan={ columnCount } /></tr>
			) }

			{ virtualItems.map( ( virtualRow ) =>
			{
				const row = rows[ virtualRow.index ];
				return dynamicHeight ? (
					<Fragment key={ row.id }>
						{ renderRowPair( row ) }
					</Fragment>
				) : (
					<Fragment key={ row.id }>{ renderRowPair( row ) }</Fragment>
				);
			} ) }

			{ paddingBottom > 0 && (
				<tr aria-hidden style={ { height: paddingBottom } }><td colSpan={ columnCount } /></tr>
			) }
		</tbody>
	);
}