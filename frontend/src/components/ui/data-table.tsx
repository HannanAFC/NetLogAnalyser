import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '#/lib/utils';
import { SkeletonTableRows } from './skeleton-table';
import type { SkeletonColumn } from './skeleton-table';

export type TableHeightVariant = 'sm' | 'md' | 'lg';

const TableHeightClasses: Record< TableHeightVariant, string > =
{
	'sm': 'max-h-100',
	'md': 'max-h-200',
	'lg': 'max-h-300'
};

const TableHeightPx: Record< TableHeightVariant, number > =
{
	'sm': 400,
	'md': 800,
	'lg': 1200
};

const DEFAULT_ESTIMATED_ROW_HEIGHT = 40;

interface DataTableProps< T > extends HTMLAttributes< HTMLDivElement >
{
	columns:                SkeletonColumn[ ];
	data:                   T[ ];
	renderRow:              ( item: T, index: number ) => ReactNode;
	getRowKey:              ( item: T, index: number ) => string | number;
	isLoading?:             boolean;
	isError?:               boolean;
	errorMessage?:          ReactNode;
	emptyMessage?:          ReactNode;
	loadingSkeletonCount?:  number;
	overlaySkeletonCount?:  number;
	maxHeight?:             TableHeightVariant;
	maxHeightPx?:           number;
	estimatedRowHeight?:    number;
	virtualize?:            boolean;
}

export function DataTable< T >(
{
	className,
	columns,
	data,
	renderRow,
	getRowKey,
	isLoading = false,
	isError = false,
	errorMessage,
	emptyMessage,
	loadingSkeletonCount = 20,
	overlaySkeletonCount = 10,
	maxHeight = 'md',
	maxHeightPx,
	estimatedRowHeight = DEFAULT_ESTIMATED_ROW_HEIGHT,
	virtualize = true,
	...props
}: DataTableProps< T > )
{
	const scrollRef = useRef< HTMLDivElement >( null );

	const showOverlay: boolean =
		( !isLoading && ( isError || data.length === 0 ) );

	const overlayContent: ReactNode | null =
		isError ? errorMessage ?? null : emptyMessage ?? null;

	const resolvedMaxHeightPx = maxHeightPx ?? TableHeightPx[ maxHeight ];

	return (
		<div
			className={ cn(
				'shadow-card rounded-lg border border-border overflow-hidden',
				className
			) }
			{ ...props }
		>
			<div
				ref={ scrollRef }
				className={ cn(
					'overflow-y-auto relative min-h-fit',
					TableHeightClasses[ maxHeight ],
					showOverlay && 'overflow-hidden'
				) }
			>
				<table className="w-full text-left tabular-nums">
					<thead>
						<tr className="border-b border-border bg-surface-card text-xs text-nowrap font-medium text-text-secondary">
							{ columns.map( ( col, i ) =>
							(
								<th
									key={ i }
									className={ cn( 'px-3 py-2 font-medium', col.headerClassName ) }
								>
									{ col.header }
								</th>
							) ) }
						</tr>
					</thead>

					{ isLoading &&
					(
						<SkeletonTableRows columns={ columns } count={ loadingSkeletonCount } />
					) }

					{ showOverlay && !isLoading &&
					(
						<SkeletonTableRows columns={ columns } count={ overlaySkeletonCount } />
					) }

					{ !showOverlay && !isLoading && data.length > 0 &&
					(
						virtualize ?
						(
							<VirtualisedRows
								data={ data }
								renderRow={ renderRow }
								getRowKey={ getRowKey }
								getScrollElement={ ( ) => scrollRef.current }
								estimatedRowHeight={ estimatedRowHeight }
								columnCount={ columns.length }
								maxHeightPx={ resolvedMaxHeightPx }
							/>
						)
						:
						(
							<tbody>
								{ data.map( ( item, index ) =>
								(
									renderRow( item, index )
								) ) }
							</tbody>
						)
					) }
				</table>

				<div
					className={
						cn(
							'pointer-events-none absolute inset-x-0 bottom-0 top-0',
							'backdrop-blur-[3px] bg-linear-to-b from-transparent from-0% to-paper to-35%',
							'transition-opacity duration-150',
							showOverlay ? 'opacity-100' : 'opacity-0'
						)
					}
				/>

				<div
					className={
						cn(
							'absolute inset-x-0 top-[50%] left-[50%] -translate-1/2 w-max max-w-4/5',
							showOverlay ? 'opacity-100' : 'opacity-0'
						)
					}
				>
					{ overlayContent }
				</div>
			</div>
		</div>
	);
}

interface VirtualisedRowsProps< T >
{
	data:                T[ ];
	renderRow:           ( item: T, index: number ) => ReactNode;
	getRowKey:           ( item: T, index: number ) => string | number;
	getScrollElement:    ( ) => HTMLElement | null;
	estimatedRowHeight:  number;
	columnCount:         number;
	maxHeightPx:         number;
}

function VirtualisedRows< T >(
{
	data,
	renderRow,
	getRowKey,
	getScrollElement,
	estimatedRowHeight,
	columnCount,
	maxHeightPx
}: VirtualisedRowsProps< T > )
{
	const virtualizer = useVirtualizer(
	{
		count:            data.length,
		getScrollElement: getScrollElement,
		estimateSize:     ( ) => estimatedRowHeight,
		overscan:         10,
		getItemKey:       ( index ) => getRowKey( data[ index ], index ),
		initialRect:
		{
			width:  0,
			height: maxHeightPx
		}
	} );

	const virtualItems = virtualizer.getVirtualItems( );

	const paddingTop = virtualItems.length > 0
		? virtualItems[ 0 ].start
		: 0;
	const paddingBottom = virtualItems.length > 0
		? virtualizer.getTotalSize( ) - virtualItems[ virtualItems.length - 1 ].end
		: 0;

	return (
		<tbody>
			{ paddingTop > 0 &&
			(
				<tr aria-hidden style={ { height: paddingTop } }>
					<td colSpan={ columnCount } />
				</tr>
			) }

			{ virtualItems.map( ( virtualRow ) =>
			(
				renderRow( data[ virtualRow.index ], virtualRow.index )
			) ) }

			{ paddingBottom > 0 &&
			(
				<tr aria-hidden style={ { height: paddingBottom } }>
					<td colSpan={ columnCount } />
				</tr>
			) }
		</tbody>
	);
}
