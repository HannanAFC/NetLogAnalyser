// features/analytics/query-key.ts
import type { GeoParams, ProtocolsParams, SummaryParams, TimeseriesParams, TopTalkersParams, AnomaliesParams } from '#/features/analytics/schemas';

export const analyticsKeys = {
	all:         [ 'analytics' ] as const,
	summary:     ( params: SummaryParams )     => [ ...analyticsKeys.all, 'summary', params ] as const,
	timeseries:  ( params: TimeseriesParams )  => [ ...analyticsKeys.all, 'timeseries', params ] as const,
	topTalkers:  ( params: TopTalkersParams )  => [ ...analyticsKeys.all, 'top-talkers', params ] as const,
	protocols:   ( params: ProtocolsParams )   => [ ...analyticsKeys.all, 'protocols', params ] as const,
	geo:         ( params: GeoParams )         => [ ...analyticsKeys.all, 'geo', params ] as const,
	anomalies:   ( params: AnomaliesParams )   => [ ...analyticsKeys.all, 'anomalies', params ] as const
};