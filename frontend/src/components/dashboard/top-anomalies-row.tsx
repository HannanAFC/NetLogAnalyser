import type { LogEntry } from '#/lib/logs/types';
import { AnomalyIndicator } from '../live-feed/anomaly-indicator';

export function TopAnomaliesRow( { row }: { row: LogEntry } )
{
    return (
        <tr
            className="border-b border-border last:border-0 hover:bg-inset transition-colors duration-150"
            key={ row.id }
        >
            <td className="whitespace-nowrap px-3 py-2 font-mono text-sm">
                { row.src_ip }:{ row.src_port }
            </td>
            <td className="whitespace-nowrap px-3 py-2 text-text-secondary">→</td>
            <td className="whitespace-nowrap px-3 py-2 font-mono text-sm">
                { row.dst_ip }:{ row.dst_port }
            </td>
            <td className="whitespace-nowrap px-3 py-2">
                <AnomalyIndicator score={ row.anomaly_score } reasons={ row.anomaly_reasons } />
            </td>
        </tr>
    );
}