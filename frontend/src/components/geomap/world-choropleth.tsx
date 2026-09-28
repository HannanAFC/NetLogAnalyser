import { scaleQuantize } from 'd3-scale';
import { ComposableMap, Geographies, Geography, ZoomableGroup } from 'react-simple-maps';
import worldAtlas from 'world-atlas/countries-110m.json';

import { numericToAlpha2, numericToName } from '#/lib/geomap/country-codes';
import type { GeoEntry } from '#/lib/analytics/types';
import { Card } from '../ui/card';
import { useState } from 'react';
import { MapPopup } from './map-popup';
import { useDebounce } from '#/lib/utils';

interface WorldChoroplethProps
{
	rows: GeoEntry[ ];
}

interface TooltipPositionProps
{
	x: number;
	y: number;
}

interface ExtendedCountryInfo extends GeoEntry
{
	countryName: string;
}

export function WorldChoropleth( { rows }: WorldChoroplethProps )
{
	const byCountry = new Map( rows.map( ( row ) => [ row.country_code as string, row ] ) );
	const maxPct    = Math.max( 1, ...rows.map( ( row ) => row.packet_percentage ) );
	const bucketOf  = scaleQuantize< number >( ).domain( [ 0, maxPct ] ).range( [ 0, 1, 2, 3, 4 ] );

	const [ hoveredCountry, setHoveredCountry ]   = useState< ExtendedCountryInfo | null >( null );
	const [ tooltipPosition, setTooltipPosition ] = useState< TooltipPositionProps >(
	{
		x: 0,
		y: 0
	} );

	const debouncedPosition = useDebounce( tooltipPosition, 150 );
	const debouncedCountry  = useDebounce( hoveredCountry, 150 );

	return (
		<Card>
		<ComposableMap projectionConfig={ { scale: 140 } }>
			<ZoomableGroup zoom={ 1.2 }>
			<Geographies geography={ worldAtlas }>
				{ ( { geographies } ) =>
					geographies.map( ( geo ) =>
                    {
						const alpha2      = numericToAlpha2( String( geo.id ) );
						const countryName = numericToName( String( geo.id ) );
						const row         = alpha2 ? byCountry.get( alpha2 ) : null;
						const bucket      = row ? bucketOf( row.packet_percentage ) : null;
						const fill        = bucket === null
							? `choropleth-empty`
							: `choropleth-${ bucket }`;

						const extendedCountry: ExtendedCountryInfo | null =
						row && countryName ?
						{
							...row,
							countryName: countryName
						} : null;

						return (
							<Geography
								key={ geo.rsmKey }
								geography={ geo }
								className={ `choropleth ${ fill }` }
								onMouseEnter={ ( event ) =>
								{
									setHoveredCountry( extendedCountry );
									setTooltipPosition(
									{
										x: event.clientX,
										y: event.clientY
									} );
								} }
								onMouseMove={ ( event ) =>
								{
									setTooltipPosition(
									{
										x: event.clientX,
										y: event.clientY
									} );
								} }
								onMouseLeave={ ( ) =>
								{
									setHoveredCountry( null );
								} }
							/>
						);
					} )
				}
			</Geographies>
			</ZoomableGroup>
		</ComposableMap>
		{ debouncedCountry &&
		(
			<MapPopup
				left={ debouncedPosition.x + 10 }
				top={ debouncedPosition.y + 10 }
			>
				<strong>{ debouncedCountry.countryName }</strong>
				<div>Packets: { debouncedCountry.count }</div>
				<div>Percentage: { debouncedCountry.packet_percentage.toFixed( 2 ) }%</div>
			</MapPopup>
		) }
		</Card>
	);
}