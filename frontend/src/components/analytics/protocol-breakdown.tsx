import { useMemo } from 'react';
import { scaleBand, scaleLinear } from 'd3-scale';
import { barY, defineChart } from '@tanstack/charts';
import { Chart } from '@tanstack/react-charts';
import { useProtocols } from '#/features/analytics/hooks';
import type { TimeRangeParams } from '#/features/analytics/schemas';
import { Card } from '../ui/card';
import { DataTable } from '../ui/data-table';
import type { PortEntry } from '#/lib/analytics/types';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';
import type { SkeletonColumn } from '../ui/skeleton-table';

interface ProtocolBreakdownProps
{
	range: TimeRangeParams;
}

const COLUMNS: SkeletonColumn[ ] =
[
	{ header: 'Port' },
	{ header: 'Count' }
];

function PortRow( { row }: { row: PortEntry } )
{
	return (
		<tr className="border-b border-border last:border-0 hover:bg-inset transition-colors duration-150">
			<td className="whitespace-nowrap px-3 py-2 text-sm">{ row.port }</td>
			<td className="whitespace-nowrap px-3 py-2 text-sm">{ row.count.toLocaleString( ) }</td>
		</tr>
	);
}

export function ProtocolBreakdown( { range }: ProtocolBreakdownProps )
{
	const { data, isPending, isError } = useProtocols( range );

	const definition = useMemo( ( ) =>
    {
		const rows = data?.by_protocol ?? [ ];
		return defineChart(
        {
			marks: [ barY( rows, { id: 'protocols', x: 'protocol', y: 'count' } ) ],
			x: { scale: scaleBand },
			y: { scale: scaleLinear, nice: true, grid: true, axis: { label: 'Packets' } }
		} );
	}, [ data ] );

	if ( isPending ) return <div className="h-55 animate-pulse" aria-hidden="true" />;
	if ( isError )   return <p className="text-text-secondary text-sm">Couldn't load protocol breakdown.</p>;

	return (
		<Card>
			<Chart definition={ definition } height={ 220 } ariaLabel="Packets by protocol" />

			<DataTable< PortEntry >
				className="mt-4 w-full"
				columns={ COLUMNS }
				data={ data.top_dst_ports }
				renderRow={ ( row ) => <PortRow key={ row.port } row={ row } /> }
				getRowKey={ ( row ) =>
				{
					return row.port;
				} }
				isLoading={ isPending }
				isError={ isError }
				errorMessage={ <TableLoadingErrorMessage>An error occurred whilst loading the port breakdown.</TableLoadingErrorMessage> }
				emptyMessage={ <TableNoRecentsErrorMessage>Port breakdown not available for the current time range.</TableNoRecentsErrorMessage> }
				maxHeight='md'
				virtualize={ false }
			/>
		</Card>
	);
}