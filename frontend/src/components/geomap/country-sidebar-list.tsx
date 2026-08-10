// components/geomap/country-sidebar-list.tsx
import type { GeoEntry } from '#/lib/analytics/types';
import { DataTable } from '../ui/data-table';
import type { SkeletonColumn } from '../ui/skeleton-table';
import { TableLoadingErrorMessage } from '../ui/table-loading-error-message';
import { TableNoRecentsErrorMessage } from '../ui/table-no-recents-error-message';

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

const COLUMNS: SkeletonColumn[ ] =
[
	{ header: 'Location' },
	{ header: 'Count' }
];

function GeoRow( { row }: { row: GeoEntry } )
{
	return (
		<tr className="border-b border-border last:border-0 hover:bg-inset transition-colors duration-150">
			<td className="whitespace-nowrap px-3 py-2 font-mono text-sm">{ row.country_code ?? GEO_STATUS_LABEL[ row.geo_status ] }</td>
			<td className="whitespace-nowrap px-3 py-2 text-sm">{ row.count.toLocaleString( ) }</td>
		</tr>
	);
}

export function CountrySidebarList( { rows, isLoading, isError }: CountrySidebarListProps )
{
	return (
		<DataTable< GeoEntry >
			columns={ COLUMNS }
			data={ rows }
			renderRow={ ( row, _index ) => <GeoRow row={ row } key={ `${ row.country_code }|${ row.geo_status }` } /> }
			getRowKey={ ( row, _index ) =>
			{
				return `${ row.country_code }|${ row.geo_status }`;
			} }
			isLoading={ isLoading }
			isError={ isError }
			errorMessage={ <TableLoadingErrorMessage>Unable to load geo data.</TableLoadingErrorMessage> }
			emptyMessage={ <TableNoRecentsErrorMessage>No geo data for the given time range.</TableNoRecentsErrorMessage> }
			maxHeight='md'
			virtualize={ false }
		/>
	);
}