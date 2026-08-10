import { useInfiniteQuery, useQuery } from '@tanstack/react-query';

import {
	anomaliesInfiniteQueryOptions,
	geoQueryOptions,
	protocolsQueryOptions,
	summaryQueryOptions,
	timeseriesQueryOptions,
	topTalkersQueryOptions
} from './queries';
import type {
	AnomaliesFilterParams,
	GeoParams,
	TimeRangeParams,
	TimeseriesParams,
	TopTalkersParams
} from './schemas';

export function useSummary( params: TimeRangeParams )
{
	return useQuery( summaryQueryOptions( params ) );
}

export function useTimeseries( params: TimeseriesParams )
{
	return useQuery( timeseriesQueryOptions( params ) );
}

export function useTopTalkers( params: TopTalkersParams )
{
	return useQuery( topTalkersQueryOptions( params ) );
}

export function useProtocols( params: TimeRangeParams )
{
	return useQuery( protocolsQueryOptions( params ) );
}

export function useGeo( params: GeoParams )
{
	return useQuery( geoQueryOptions( params ) );
}

export function useAnomalies( params: AnomaliesFilterParams )
{
	return useInfiniteQuery( anomaliesInfiniteQueryOptions( params ) );
}
