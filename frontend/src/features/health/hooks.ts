import { useQuery } from '@tanstack/react-query';
import { healthQueryOptions } from './queries';

export function useAppVersion( )
{
	const { data } = useQuery( healthQueryOptions );
	return data?.version;
}