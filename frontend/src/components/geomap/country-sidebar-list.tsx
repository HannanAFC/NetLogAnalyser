// components/geomap/country-sidebar-list.tsx
import { createColumnHelper, metaHelper, tableFeatures, useTable } from '@tanstack/react-table';
import { useMemo } from 'react';
import { Card } from '../ui/card';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';
import { TanStackDataTable } from '../ui/tanstack-data-table';
import type { SkeletonColumn } from '../ui/skeleton-table';
import type { GeoEntry } from '#/lib/analytics/types';

const GEO_STATUS_LABEL: Record< string, string > = {
	private:     'Private IP',
	unresolved:  'Unresolved',
	unavailable: 'Lookup unavailable',
	resolved:    'Resolved'
};

interface CountrySidebarListProps
{
	rows:      GeoEntry[ ];
	isLoading: boolean;
	isError:   boolean;
}

const SKELETON_COLUMNS: SkeletonColumn[ ] =
[
	{ },
	{ }
];

interface CountryTableColumnMeta
{
	className?: string;
}

const features = tableFeatures(
{
	columnMeta: metaHelper< CountryTableColumnMeta >( )
} );

const columnHelper = createColumnHelper< typeof features, GeoEntry >( );

export function CountrySidebarList( { rows, isLoading, isError }: CountrySidebarListProps )
{
	const columns = useMemo( ( ) =>
		columnHelper.columns(
		[
			columnHelper.accessor(
				'country_code',
				{
					header: 'Location',
					meta:   { className: 'font-mono text-sm' },
					cell:   ( info ) => info.getValue( ) ?? GEO_STATUS_LABEL[ info.row.original.geo_status ]
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

	const table = useTable(
	{
		key:                'country-table',
		features:           features,
		columns:            columns,
		data:               rows
	} );

	return (
		<Card>
			<TanStackDataTable
				table={ table }
				skeletonColumns={ SKELETON_COLUMNS }
				isLoading={ isLoading }
				isError={ isError }
				errorMessage={ <TableLoadingErrorMessage>Unable to load geo data.</TableLoadingErrorMessage> }
				emptyMessage={ <TableNoRecentsErrorMessage>No geo data for the given time range.</TableNoRecentsErrorMessage> }
				maxHeight='md'
				virtualize={ false }
				className='h-full min-h-30'
			/>
		</Card>
	);
}