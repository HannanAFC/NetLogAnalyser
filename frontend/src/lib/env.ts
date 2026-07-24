/**
 * Central, typed access to build-time env vars. Never read
 * `import.meta.env` directly elsewhere - go through this module so a
 * missing var fails loudly at startup instead of silently at request time.
 */
function required( name: string, value: string | undefined ): string
{
	if ( !value )
	{
		throw new Error( `Missing required env var: ${ name }` );
	}
	return value;
}

export const env =
{
	apiBaseUrl: required( 'VITE_API_BASE_URL', import.meta.env.VITE_API_BASE_URL ),
	wsBaseUrl: required( 'VITE_WS_BASE_URL', import.meta.env.VITE_WS_BASE_URL )
};