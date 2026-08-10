import type { LogEntry } from '#/lib/logs/types';

export type TimeBucket = 'minute' | 'hour' | 'day';

export type Direction = 'src' | 'dst';

export type TopTalkersMetric = 'packets' | 'bytes';

export interface SummaryResponse
{
	start:              string;
	end:                string;
	total_packets:      number;
	unique_src_ips:     number;
	unique_dst_ips:     number;
	avg_anomaly_score:  number;
	high_anomaly_count: number;
	total_bytes:        number;
}

export interface TimeSeriesPoint
{
	ts:                string;
	count:             number;
	avg_anomaly_score: number;
	total_bytes:       number;
}

export interface TimeSeriesResponse
{
	bucket: TimeBucket;
	points: TimeSeriesPoint[ ];
}

export interface TopTalkerEntry
{
	ip:                string;
	count:             number;
	avg_anomaly_score: number;
	total_bytes:       number;
}

export interface TopTalkersResponse
{
	direction: Direction;
	metric:    TopTalkersMetric;
	rows:      TopTalkerEntry[ ];
}

export interface ProtocolEntry
{
	protocol:          string;
	count:             number;
	packet_percentage: number;
}

export interface PortEntry
{
	port:  number;
	count: number;
}

export interface ProtocolsResponse
{
	by_protocol:   ProtocolEntry[ ];
	top_dst_ports: PortEntry[ ];
}

export interface GeoEntry
{
	country_code:      string | null;
	geo_status:        string;
	count:             number;
	packet_percentage: number;
}

export interface GeoResponse
{
	rows:      GeoEntry[ ];
	direction: Direction;
}

export interface AnomaliesResponse
{
	rows:        LogEntry[ ];
	next_cursor: string | null;
	has_more:    boolean;
}
