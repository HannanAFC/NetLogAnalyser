import type {
	AnomaliesParams,
	GeoParams,
	TimeRangeParams,
	TimeseriesParams,
	TopTalkersParams
} from './schemas';

export const analyticsKeys =
{
	all:         [ 'analytics' ] as const,
	summary:     ( params: TimeRangeParams ) => [ ...analyticsKeys.all, 'summary', params ] as const,
	timeseries:  ( params: TimeseriesParams ) => [ ...analyticsKeys.all, 'timeseries', params ] as const,
	topTalkers:  ( params: TopTalkersParams ) => [ ...analyticsKeys.all, 'top-talkers', params ] as const,
	protocols:   ( params: TimeRangeParams ) => [ ...analyticsKeys.all, 'protocols', params ] as const,
	geo:         ( params: GeoParams )        => [ ...analyticsKeys.all, 'geo', params ] as const,
	anomalies:   ( params: AnomaliesParams )  => [ ...analyticsKeys.all, 'anomalies', params ] as const
};
