import { useMemo } from 'react';
import { scaleBand, scaleLinear } from 'd3-scale';
import { barY, defineChart } from '@tanstack/charts';
import { Chart } from '@tanstack/react-charts';
import { useProtocols } from '#/features/analytics/hooks';
import type { TimeRangeParams } from '#/features/analytics/schemas';
import { Card } from '../ui/card';
import type { PortEntry } from '#/lib/analytics/types';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';
import type { SkeletonColumn } from '../ui/skeleton-table';
import { TanStackDataTable } from '../ui/tanstack-data-table';
import {
	tableFeatures,
	useTable,
	createColumnHelper
} from '@tanstack/react-table';

interface ProtocolBreakdownProps
{
	range: TimeRangeParams;
}

const SKELETON_COLUMNS: SkeletonColumn[ ] =
[
	{ },
	{ }
];

const EMPTY_ROWS: PortEntry[ ] = [ ];

const features = tableFeatures( { } );

const columnHelper = createColumnHelper< typeof features, PortEntry >( );

export function ProtocolBreakdown( { range }: ProtocolBreakdownProps )
{
	const columns = useMemo( ( ) =>
		columnHelper.columns(
		[
			columnHelper.accessor(
				'port',
				{
					header: 'Port',
					cell:   ( info ) => info.getValue( )
				}
			),
			columnHelper.accessor(
				'count',
				{
					header: 'Count',
					cell:   ( info ) => info.getValue( )
				}
			)
		] ),
		[ ]
	);

	const { data, isLoading, isError } = useProtocols( range );

	const table = useTable(
	{
		key:                'anomalies-table',
		features:           features,
		columns:            columns,
		data:               data?.top_dst_ports ?? EMPTY_ROWS
	} );

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

	if ( isLoading ) return <div className="h-55 animate-pulse" aria-hidden="true" />;
	if ( isError )   return <p className="text-text-secondary text-sm">Couldn't load protocol breakdown.</p>;

	return (
		<Card>
			<Chart definition={ definition } height={ 220 } ariaLabel="Packets by protocol" />
			<TanStackDataTable
				table={ table }
				skeletonColumns={ SKELETON_COLUMNS }
				isLoading={ isLoading }
				isError={ isError }
				errorMessage={ <TableLoadingErrorMessage>An error occurred whilst loading the port breakdown.</TableLoadingErrorMessage> }
				emptyMessage={ <TableNoRecentsErrorMessage>Port breakdown not available for the current time range.</TableNoRecentsErrorMessage> }
				maxHeight='md'
				virtualize={ false }
			/>
		</Card>
	);
}