export function logsQueryKey( limit: number )
{
	return [ 'logs', limit ] as const;
}