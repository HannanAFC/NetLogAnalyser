import { queryOptions, infiniteQueryOptions } from '@tanstack/react-query';
import { analyticsKeys } from './query-key';
import {
	getSummaryRequest,
	getTimeseriesRequest,
	getTopTalkersRequest,
	getProtocolsRequest,
	getGeoRequest,
	getAnomaliesRequest
} from './api';
import type {
	AnomaliesParams,
	GeoParams,
	TimeRangeParams,
	TimeseriesParams,
	TopTalkersParams
} from './schemas';

export function summaryQueryOptions( params: TimeRangeParams )
{
	return queryOptions(
	{
		queryKey:  analyticsKeys.summary( params ),
		queryFn:   ( ) => getSummaryRequest( params ),
		staleTime: 30_000 // If redis TTL changes this also should change
	} );
}

export function timeseriesQueryOptions( params: TimeseriesParams )
{
	return queryOptions(
	{
		queryKey:  analyticsKeys.timeseries( params ),
		queryFn:   ( ) => getTimeseriesRequest( params ),
		staleTime: 30_000
	} );
}

export function topTalkersQueryOptions( params: TopTalkersParams )
{
	return queryOptions(
	{
		queryKey: analyticsKeys.topTalkers( params ),
		queryFn:  ( ) => getTopTalkersRequest( params )
	} );
}

export function protocolsQueryOptions( params: TimeRangeParams )
{
	return queryOptions(
	{
		queryKey: analyticsKeys.protocols( params ),
		queryFn:  ( ) => getProtocolsRequest( params )
	} );
}

export function geoQueryOptions( params: GeoParams )
{
	return queryOptions(
	{
		queryKey: analyticsKeys.geo( params ),
		queryFn:  ( ) => getGeoRequest( params )
	} );
}

export function anomaliesInfiniteQueryOptions( params: AnomaliesParams )
{
	return infiniteQueryOptions(
	{
		queryKey:         analyticsKeys.anomalies( params ),
		queryFn:          ( { pageParam } ) => getAnomaliesRequest( { ...params, cursor: pageParam } ),
		initialPageParam: undefined as string | undefined,
		getNextPageParam: ( lastPage ) => lastPage.has_more ? ( lastPage.next_cursor ?? undefined ) : undefined
	} );
}