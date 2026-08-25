declare global
{
	interface Window
	{
		__ENV__:
		{
			BACKEND_PORT?: string
			API_BASE_URL?: string
			WS_BASE_URL?:  string
			APP_VERSION?:  string
		} | undefined
	}
}

function resolveApiBaseUrl( ): string
{
	const { BACKEND_PORT, API_BASE_URL } = window.__ENV__ ?? { };

	// Self-host: browser and backend share a host, only the port varies.
	if ( BACKEND_PORT )
	{
		return `${ window.location.protocol }//${ window.location.hostname }:${ BACKEND_PORT }`;
	}

	// Render / local dev: config.js carries the full URL directly.
	if ( API_BASE_URL ) return API_BASE_URL;

	throw new Error( 'env.ts: no API base URL available - config.js is missing or malformed' );
}

function resolveWsBaseUrl( ): string
{
	const { BACKEND_PORT, WS_BASE_URL } = window.__ENV__ ?? { };

	if ( BACKEND_PORT )
	{
		const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		return `${ wsProtocol }//${ window.location.hostname }:${ BACKEND_PORT }/ws`;
	}

	if ( WS_BASE_URL ) return WS_BASE_URL;

	throw new Error( 'env.ts: no WS base URL available - config.js is missing or malformed' );
}

export const env =
{
	apiBaseUrl: resolveApiBaseUrl( ),
	wsBaseUrl:  resolveWsBaseUrl( )
};