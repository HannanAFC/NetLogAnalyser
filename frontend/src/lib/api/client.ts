import type { AxiosError } from 'axios';
import axios from 'axios';
import { sessionQueryKey } from '../auth/session-key';
import { tokenStore } from '../auth/token-store';
import type { RefreshResponse } from '../auth/types';
import { env } from '../env';
import { queryClient } from './query-client';

declare module 'axios'
{
	export interface InternalAxiosRequestConfig
	{
		/** Marks a request that already went through one refresh-and-retry cycle. */
		_retry?: boolean;
	}
}

export const apiClient = axios.create(
{
	baseURL: env.apiBaseUrl,
	// Sends the httpOnly refresh cookie (path=/auth) on every request.
	// required for /auth/refresh and /auth/logout.
	withCredentials: true
});

apiClient.interceptors.request.use( ( config ) => 
{
	const token = tokenStore.get( );
	if ( token )
	{
		config.headers.Authorization = `Bearer ${ token }`;
	}
	return config;
});

// Concurrent requests that all 401 at once must share a single refresh
// call, not each trigger their own - that would race token rotation on
// the backend and fail the whole family.
let refreshPromise: Promise< string > | null = null;

function refreshAccessToken( ): Promise< string >
{
	if ( !refreshPromise )
	{
		refreshPromise = axios
		.post< RefreshResponse >( `${ env.apiBaseUrl }/auth/refresh`, null,
		{
			withCredentials: true,
		})
		.then( ( { data } ) =>
		{
			tokenStore.set( data.access_token );
			return data.access_token;
		})
		.catch( ( error ) =>
		{
			// Refresh cookie is missing, expired, or its family was revoked
			// just send user to login
			tokenStore.set( null );
			queryClient.setQueryData( sessionQueryKey, null );
			throw error;
		})
		.finally( ( ) => 
		{
			refreshPromise = null;
		});
	}
	return refreshPromise;
}

apiClient.interceptors.response.use(
	( response ) => response,
	async ( error: AxiosError ) =>
	{
		const original = error.config;
		const status = error.response?.status;

		const isAuthEndpoint = original?.url?.includes( '/auth/refresh' ) || original?.url?.includes( '/auth/login' );

		if ( !original || status !== 401 || original._retry || isAuthEndpoint )
		{
			return Promise.reject( error );
		}

		original._retry = true;

		try {
			const token = await refreshAccessToken( );
			original.headers.Authorization = `Bearer ${token}`;
			return apiClient( original );
		}
		catch ( refreshError )
		{
			return Promise.reject( refreshError );
		}
	}
);
