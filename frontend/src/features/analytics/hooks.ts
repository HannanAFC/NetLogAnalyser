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
	ProtocolsParams,
	SummaryParams,
	TimeseriesParams,
	TopTalkersParams
} from './schemas';

export function useSummary( params: SummaryParams )
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

export function useProtocols( params: ProtocolsParams )
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