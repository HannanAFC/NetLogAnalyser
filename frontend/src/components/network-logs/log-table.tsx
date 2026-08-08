import type { LogEntry } from '#/lib/logs/types';
import { LogEntryRow } from './log-entry-row';
import { SkeletonLog } from '../skeletons/skeleton-log';
import { getLogEntryKey } from '#/lib/logs/entry-key';
import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { ReactNode } from 'react';

type TableHeightVariant = 'sm' | 'md' | 'lg';

const TableHeightVariantClasses: Record< TableHeightVariant, string > =
{
    'sm': 'max-h-100',
    'md': 'max-h-200',
    'lg': 'max-h-300'
};

const TableHeightVariantPx: Record< TableHeightVariant, number > =
{
    'sm': 400,
    'md': 800,
    'lg': 1200
};

const ESTIMATED_ROW_HEIGHT = 40;

const COLUMN_COUNT = 9;

interface LogTableProps
{
	isLoading:                boolean;
	isError:                  boolean;
	loadingErrorMessage:      ReactNode;
	noRecentLogsErrorMessage: ReactNode;
	entries:                  LogEntry[ ]
	maxHeight?:               TableHeightVariant;
}

function SkeletonRows( { count = 20 }: { count?: number } )
{
	return (
		<>
			{ Array.from( { length: count }, ( _, i ) =>
			(
				<SkeletonLog key={ i } />
			) ) }
		</>
	);
}

function FailureStructure( { failureMessage }: { failureMessage: ReactNode } )
{
    return (
        <div className="relative overflow-hidden rounded-lg border border-border">
            <table className="w-full text-left">
                <LogTableHead />
                <tbody>
                    <SkeletonRows count={10} />
                </tbody>
            </table>

            <div className="pointer-events-none absolute inset-x-0 bottom-0 top-0 backdrop-blur-[3px] bg-linear-to-b from-transparent from-0% to-paper to-35%" />

            <div className="absolute inset-x-0 top-[50%] left-[50%] -translate-1/2 w-max max-w-4/5">
                {failureMessage}
            </div>
        </div>
    );
}

function LogTableHead( )
{
	return (
		<thead>
			<tr className="border-b border-border bg-surface-card text-xs font-medium text-text-secondary">
				<th className="px-3 py-2 font-medium">Time</th>
				<th className="px-3 py-2 font-medium">Source</th>
				<th className="px-3 py-2" />
				<th className="px-3 py-2 font-medium">Destination</th>
				<th className="px-3 py-2 font-medium">Protocol</th>
				<th className="px-3 py-2 text-right font-medium">Size</th>
				<th className="px-3 py-2 font-medium">Source country</th>
				<th className="px-3 py-2 font-medium">Destination country</th>
				<th className="px-3 py-2 font-medium">Anomaly</th>
			</tr>
		</thead>
	);
}

function VirtualisedLogRows( { entries, scrollRef, maxHeight }: { entries: LogEntry[ ]; scrollRef: React.RefObject< HTMLDivElement | null >; maxHeight: TableHeightVariant } )
{
	const virtualizer = useVirtualizer(
	{
		count:            entries.length,
		getScrollElement: ( ) => scrollRef.current,
		estimateSize:     ( ) => ESTIMATED_ROW_HEIGHT,
		overscan:         10,
		getItemKey:       ( index ) => getLogEntryKey( entries[ index ] ),
		initialRect:
		{
			width:  0,
			height: TableHeightVariantPx[ maxHeight ]
		}
	} );

	const virtualItems = virtualizer.getVirtualItems( );

	const paddingTop = virtualItems.length > 0 ? virtualItems[ 0 ].start : 0;
	const paddingBottom = virtualItems.length > 0
		? virtualizer.getTotalSize( ) - virtualItems[ virtualItems.length - 1 ].end
		: 0;

	return (
		<tbody>
			{ paddingTop > 0 &&
			(
				<tr aria-hidden style={ { height: paddingTop } }>
					<td colSpan={ COLUMN_COUNT } />
				</tr>
			) }

			{ virtualItems.map( ( virtualRow ) =>
			(
				<LogEntryRow key={ virtualRow.key } entry={ entries[ virtualRow.index ] } />
			) ) }

			{ paddingBottom > 0 &&
			(
				<tr aria-hidden style={ { height: paddingBottom } }>
					<td colSpan={ COLUMN_COUNT } />
				</tr>
			) }
		</tbody>
	);
}

export function LogTable(
{
	isLoading,
	isError,
	loadingErrorMessage,
	noRecentLogsErrorMessage,
	entries,
	maxHeight = 'md'
}: LogTableProps )
{
	const scrollRef = useRef< HTMLDivElement >( null );

	return (
		<div className="flex flex-col gap-8 mt-8">
			{ isError && !isLoading && entries.length === 0 &&
			(
				<FailureStructure failureMessage={ loadingErrorMessage } />
			) }

			{ !isLoading && !isError && entries.length === 0 &&
			(
				<FailureStructure failureMessage={ noRecentLogsErrorMessage } />
			) }

			{ isLoading &&
			(
				<div className={ `overflow-auto rounded-lg border border-border ${ TableHeightVariantClasses[ maxHeight ] }` }>
					<table className="w-full text-left">
						<LogTableHead />
						<tbody>
							<SkeletonRows />
						</tbody>
					</table>
				</div>
			) }

			{ entries.length > 0 &&
			(
				<div
					ref={ scrollRef }
					className={ `overflow-auto rounded-lg border border-border ${ TableHeightVariantClasses[ maxHeight ] }` }
				>
					<table className="w-full text-left tabular-nums">
						<LogTableHead />
						<VirtualisedLogRows entries={ entries } scrollRef={ scrollRef } maxHeight={ maxHeight } />
					</table>
				</div>
			) }
		</div>
	);
}