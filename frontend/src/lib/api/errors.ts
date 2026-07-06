/**
 * Pull a human-readable message out of an Axios error returned by a FastAPI backend.
 *
 * FastAPI sends errors in two shapes:
 * - `HTTPException`  →  `error.response.data.detail` is a plain string
 * - Pydantic `ValidationError`  →  `error.response.data.detail` is `{ msg: string }[]`
 *
 * Falls back to `Error.message` for non-Axios / network-level errors.
 */
export function apiError( error: unknown ): string | undefined
{

	if ( error && typeof error === 'object' && 'response' in error )
	{
		const axiosErr = error as { response?: { data?: { detail?: unknown } } };
		const detail = axiosErr.response?.data?.detail;
		if ( typeof detail === 'string' ) return detail;
		if (
			Array.isArray( detail ) &&
			detail.length > 0 &&
			typeof detail[ 0 ] === 'object' &&
			detail[ 0 ] !== null &&
			'msg' in detail[ 0 ]
		)
			return ( detail[ 0 ] as { msg: string } ).msg;
	}
	if ( error instanceof Error ) return error.message;
	return undefined;
}
