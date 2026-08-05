export type Protocol = 'TCP' | 'UDP' | 'ICMP' | 'OTHER';

export interface AnomalyReason
{
    name:   string;
    score:  number;
    detail: string | null;
}

export interface LogEntry
{
    id?:               number;
    src_ip:            string;
    dst_ip:            string;
    src_port:          number;
    dst_port:          number;
    protocol:          Protocol;
    packet_size_bytes: number;
    flags:             string | null;
    country_code:      string | null;
    anomaly_score:     number;
    anomaly_reasons:   Array< AnomalyReason >;
    captured_at:       string;
}

export interface GetLogsResponse
{
    entries:     LogEntry[ ];
    next_cursor: string | null;
    has_more:    boolean;
}