import { useState } from 'react';

import { useTopTalkers } from '#/features/analytics/hooks';
import { Button } from '#/components/ui/button';
import type { Direction, Metric, TimeRangeParams } from '#/features/analytics/schemas';
import { Card } from '../ui/card';
import type { SkeletonColumn } from '../ui/skeleton-table';
import type { TopTalkerEntry } from '#/lib/analytics/types';
import { DataTable } from '../ui/data-table';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';

interface TopTalkersTableProps
{
	range: TimeRangeParams;
}

const COLUMNS: SkeletonColumn[ ] =
[
	{ header: 'IP' },
	{ header: 'Packets' },
	{ header: 'Bytes' },
	{ header: '	Avg score' }
];

function TopTalkerRow( { row }: { row: TopTalkerEntry } )
{
	return (
		<tr className="border-b border-border last:border-0 hover:bg-inset transition-colors duration-150">
			<td className="whitespace-nowrap px-3 py-2 font-mono text-sm">{ row.ip }</td>
			<td className="whitespace-nowrap px-3 py-2 text-sm">{ row.count.toLocaleString( ) }</td>
			<td className="whitespace-nowrap px-3 py-2 text-sm">{ row.total_bytes.toLocaleString( ) }</td>
			<td className="whitespace-nowrap px-3 py-2 text-sm">{ row.avg_anomaly_score.toFixed( 2 ) }</td>
		</tr>
	);
}

export function TopTalkersTable( { range }: TopTalkersTableProps )
{
	const [ direction, setDirection ] = useState< Direction >( 'src' );
	const [ metric, setMetric ]       = useState< Metric >( 'packets' );

	const { data, isPending, isError } = useTopTalkers( { ...range, direction, metric, limit: 10 } );

	return (
		<Card>
			<div className="flex flex-wrap gap-2 pb-2">
				<div role="group" aria-label="Direction" className="flex gap-1">
					<Button type="button" variant={ direction === 'src' ? 'primary' : 'ghost' } onClick={ ( ) => setDirection( 'src' ) }>
						Source
					</Button>
					<Button type="button" variant={ direction === 'dst' ? 'primary' : 'ghost' } onClick={ ( ) => setDirection( 'dst' ) }>
						Destination
					</Button>
				</div>
				<div role="group" aria-label="Metric" className="flex gap-1">
					<Button type="button" variant={ metric === 'packets' ? 'primary' : 'ghost' } onClick={ ( ) => setMetric( 'packets' ) }>
						Packets
					</Button>
					<Button type="button" variant={ metric === 'bytes' ? 'primary' : 'ghost' } onClick={ ( ) => setMetric( 'bytes' ) }>
						Bytes
					</Button>
				</div>
			</div>

			{ isPending && <div className="h-50 animate-pulse" aria-hidden="true" /> }
			{ isError && <p className="text-text-secondary text-sm">Couldn't load top talkers.</p> }

			{ data &&
            (
				<DataTable< TopTalkerEntry >
					className="mt-4 w-full"
					columns={ COLUMNS }
					data={ data.rows }
					renderRow={ ( row, index ) => <TopTalkerRow key={ index } row={ row } /> }
					getRowKey={ ( _row, index ) =>
					{
						return index;
					} }
					isLoading={ isPending }
					isError={ isError }
					errorMessage={ <TableLoadingErrorMessage>An error occured whilst loading the top talkers.</TableLoadingErrorMessage> }
					emptyMessage={ <TableNoRecentsErrorMessage>Top talkers not available for the current time range.</TableNoRecentsErrorMessage> }
					maxHeight='md'
					virtualize={ false }
				/>
			) }
		</Card>
	);
}