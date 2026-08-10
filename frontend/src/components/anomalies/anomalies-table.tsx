import { Fragment, useState } from 'react';

import { useAnomalies } from '#/features/analytics/hooks';
import { Button } from '#/components/ui/button';
import type { AnomaliesFilterParams } from '#/features/analytics/schemas';
import { AnomalyIndicator } from '../live-feed/anomaly-indicator';

interface AnomaliesTableProps
{
	filter: AnomaliesFilterParams;
}

export function AnomaliesTable( { filter }: AnomaliesTableProps )
{
	const [ expandedId, setExpandedId ] = useState< number | null >( null );
	const { data, isPending, isError, fetchNextPage, hasNextPage, isFetchingNextPage } = useAnomalies( filter );

	if ( isPending ) return <div className="h-75 animate-pulse" aria-hidden="true" />;
	if ( isError )   return <p className="text-text-secondary text-sm">Couldn't load anomalies.</p>;

	const rows = data.pages.flatMap( ( page ) => page.rows );

	return (
		<div>
			<table className="w-full text-sm">
				<thead>
					<tr className="text-text-secondary text-left">
						<th className="pb-1 font-normal">Time</th>
						<th className="pb-1 font-normal">Source</th>
						<th className="pb-1 font-normal">Destination</th>
						<th className="pb-1 font-normal">Protocol</th>
						<th className="pb-1 font-normal">Score</th>
						<th className="pb-1 font-normal" />
					</tr>
				</thead>
				<tbody>
					{ rows.length === 0 && (
						<tr>
							<td colSpan={ 6 } className="text-text-secondary py-4 text-center">
								No anomalies above this threshold in range.
							</td>
						</tr>
					) }
					{ rows.map( ( row ) =>
					{
						const isExpanded = expandedId === row.id;
						return (
							<Fragment key={ row.id }>
								<tr className="border-border border-t">
									<td className="py-1">{ new Date( row.captured_at ).toLocaleString() }</td>
									<td className="py-1">{ row.src_ip }:{ row.src_port }</td>
									<td className="py-1">{ row.dst_ip }:{ row.dst_port }</td>
									<td className="py-1">{ row.protocol }</td>
									<td className="py-1">
                                        <AnomalyIndicator score={ row.anomaly_score } reasons={ row.anomaly_reasons } />
									</td>
									<td className="py-1">
										<Button
											type="button"
											variant="ghost"
											onClick={ () => setExpandedId( isExpanded ? null : row.id ) }
										>
											{ isExpanded ? 'Hide' : 'Details' }
										</Button>
									</td>
								</tr>
								{ isExpanded &&
                                (
									<tr className="bg-surface-card">
										<td colSpan={ 6 } className="p-3">
											<ul className="space-y-1">
												{ row.anomaly_reasons.map( ( reason ) =>
                                                (
													<li key={ reason.name } className="flex justify-between text-sm">
														<span>{ reason.name } — { reason.detail }</span>
														<span className="text-text-secondary">{ reason.score.toFixed( 2 ) }</span>
													</li>
												) ) }
												{ row.anomaly_reasons.length === 0 && (
													<li className="text-text-secondary text-sm">No individual heuristics recorded.</li>
												) }
											</ul>
										</td>
									</tr>
								) }
							</Fragment>
						);
					} ) }
				</tbody>
			</table>

			{ hasNextPage &&
            (
				<div className="pt-3 text-center">
					<Button
						type="button"
						variant="secondary"
						onClick={ ( ) => fetchNextPage( ) }
						disabled={ isFetchingNextPage }
					>
						{ isFetchingNextPage ? 'Loading…' : 'Load more' }
					</Button>
				</div>
			) }
		</div>
	);
}