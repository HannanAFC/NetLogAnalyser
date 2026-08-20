import { apiClient } from '#/lib/api/client';
import type { TimeRangeParams, TimeseriesParams, TopTalkersParams, GeoParams, AnomaliesParams } from './schemas';
import type { SummaryResponse, TimeSeriesResponse, TopTalkersResponse, ProtocolsResponse, GeoResponse, AnomaliesResponse } from '#/lib/analytics/types';

export async function getSummaryRequest( params: TimeRangeParams ): Promise< SummaryResponse >
{
	const { data } = await apiClient.get< SummaryResponse >( '/analytics/summary', { params } );
	return data;
}

export async function getTimeseriesRequest( params: TimeseriesParams ): Promise< TimeSeriesResponse >
{
	const { data } = await apiClient.get< TimeSeriesResponse >( '/analytics/timeseries', { params } );
	return data;
}

export async function getTopTalkersRequest( params: TopTalkersParams ): Promise< TopTalkersResponse >
{
	const { data } = await apiClient.get< TopTalkersResponse >( '/analytics/top-talkers', { params } );
	return data;
}

export async function getProtocolsRequest( params: TimeRangeParams ): Promise< ProtocolsResponse >
{
	const { data } = await apiClient.get< ProtocolsResponse >( '/analytics/protocols', { params } );
	return data;
}

export async function getGeoRequest( params: GeoParams ): Promise< GeoResponse >
{
	const { data } = await apiClient.get< GeoResponse >( '/analytics/geo', { params } );
	return data;
}

export async function getAnomaliesRequest( params: AnomaliesParams ): Promise< AnomaliesResponse >
{
	const { data } = await apiClient.get< AnomaliesResponse >( '/analytics/anomalies', { params } );
	return data;
}
