import { useQuery } from '@tanstack/react-query';
import { configQueryOptions } from './queries';

export function useEmailVerificationEnabled( )
{
	const { data } = useQuery( configQueryOptions );
	return data?.email_verification_enabled;
}