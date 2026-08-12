import { useState, useMemo } from 'react';
import { useTopTalkers } from '#/features/analytics/hooks';
import { Button } from '#/components/ui/button';
import type { Direction, Metric, TimeRangeParams } from '#/features/analytics/schemas';
import { Card } from '../ui/card';
import type { SkeletonColumn } from '../ui/skeleton-table';
import type { TopTalkerEntry } from '#/lib/analytics/types';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';
import { TanStackDataTable } from '../ui/tanstack-data-table';
import { createColumnHelper, tableFeatures, useTable, metaHelper } from '@tanstack/react-table';
import { AnomalyIndicator } from '../live-feed/anomaly-indicator';

interface TopTalkersTableProps
{
	range: TimeRangeParams;
}

interface TopTalkersColumnMeta
{
	className?: string;
}

const SKELETON_COLUMNS: SkeletonColumn[ ] =
[
	{ },
	{ }
];
const EMPTY_ROWS: TopTalkerEntry[ ] = [ ];

const features = tableFeatures(
{
	columnMeta: metaHelper< TopTalkersColumnMeta >( )
} );

const columnHelper = createColumnHelper< typeof features, TopTalkerEntry >( );

export function TopTalkersTable( { range }: TopTalkersTableProps )
{
	const [ direction, setDirection ] = useState< Direction >( 'src' );
	const [ metric, setMetric ]       = useState< Metric >( 'packets' );

	const columns = useMemo( ( ) =>
		columnHelper.columns(
		[
			columnHelper.accessor(
				'ip',
				{
					header: 'IP',
					meta:   { className: 'font-mono text-sm' },
					cell:   ( info ) => info.getValue( )
				}
			),
			columnHelper.accessor(
				'count',
				{
					header: 'Packets',
					cell:   ( info ) => info.getValue( )
				}
			),
			columnHelper.accessor(
				'total_bytes',
				{
					header: 'Bytes',
					meta:   { className: 'text-text-secondary tabular-nums' },
					cell:   ( info ) => info.getValue( ) + ' B'
				}
			),
			columnHelper.accessor(
				'avg_anomaly_score',
				{
					header: 'Avg score',
					cell:   ( info ) => <AnomalyIndicator score={ info.getValue( ) } reasons={ [ ] } />
				}
			)
		] ),
		[ ]
	);

	const { data, isLoading, isError } = useTopTalkers( { ...range, direction, metric, limit: 10 } );

	const table = useTable(
	{
		key:      'anomalies-table',
		features: features,
		columns:  columns,
		data:     data?.rows ?? EMPTY_ROWS
	} );

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

			<TanStackDataTable
				table={ table }
				skeletonColumns={ SKELETON_COLUMNS }
				isLoading={ isLoading }
				isError={ isError }
				errorMessage={ <TableLoadingErrorMessage>An error occurred whilst loading the top talkers.</TableLoadingErrorMessage> }
				emptyMessage={ <TableNoRecentsErrorMessage>Top talkers not available for the current time range.</TableNoRecentsErrorMessage> }
				maxHeight='md'
				virtualize={ false }
			/>
		</Card>
	);
}