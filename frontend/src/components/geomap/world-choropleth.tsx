import { scaleQuantize } from 'd3-scale';
import { ComposableMap, Geographies, Geography } from 'react-simple-maps';
import worldAtlas from 'world-atlas/countries-110m.json';

import { numericToAlpha2 } from '#/lib/geomap/country-codes';
import type { GeoEntry } from '#/lib/analytics/types';

const FILL_FALLBACKS = [ '#e0f2fe', '#93c5fd', '#3b82f6', '#1d4ed8', '#1e3a8a' ];
const EMPTY_FALLBACK = '#e5e7eb';

interface WorldChoroplethProps
{
	rows: GeoEntry[ ];
}

export function WorldChoropleth( { rows }: WorldChoroplethProps )
{
	const byCountry = new Map( rows.map( ( row ) => [ row.country_code as string, row ] ) );
	const maxPct    = Math.max( 1, ...rows.map( ( row ) => row.packet_percentage ) );
	const bucketOf  = scaleQuantize< number >( ).domain( [ 0, maxPct ] ).range( [ 0, 1, 2, 3, 4 ] );

	return (
		<ComposableMap projectionConfig={ { scale: 140 } }>
			<Geographies geography={ worldAtlas }>
				{ ( { geographies } ) =>
					geographies.map( ( geo ) =>
                    {
						const alpha2 = numericToAlpha2( String( geo.id ) );
						const row    = alpha2 ? byCountry.get( alpha2 ) : undefined;
						const bucket = row ? bucketOf( row.packet_percentage ) : null;
						const fill   = bucket === null
							? `var(--map-fill-empty, ${ EMPTY_FALLBACK })`
							: `var(--map-fill-${ bucket }, ${ FILL_FALLBACKS[ bucket ] })`;

						return (
							<Geography
								key={ geo.rsmKey }
								geography={ geo }
								style={ {
									default: { fill, stroke: 'var(--border, #ccc)', outline: 'none' },
									hover:   { fill, outline: 'none', opacity: 0.8 },
									pressed: { outline: 'none' }
								} }
							/>
						);
					} )
				}
			</Geographies>
		</ComposableMap>
	);
}