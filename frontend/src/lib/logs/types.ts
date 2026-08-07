export type Protocol = 'TCP' | 'UDP' | 'ICMP' | 'OTHER';

export type GeoStatus = 'resolved' | 'private' | 'unresolved' | 'unavailable';

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
    src_country_code:  string | null;
    dst_country_code:  string | null;
    src_geo_status:    GeoStatus;
    dst_geo_status:    GeoStatus;
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