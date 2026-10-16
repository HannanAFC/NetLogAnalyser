const raw: Record< string, string | undefined > =
{
    DOCS_URL:     process.env.DOCS_URL,
    FRONTEND_URL: process.env.FRONTEND_URL,
    BACKEND_URL:  process.env.BACKEND_URL,
    OPENAPI_URL:  process.env.OPENAPI_URL
};

function load( ): Record< keyof typeof raw, string >
{
    const missing: string[ ] = [ ];
    const invalid: string[ ] = [ ];
    const out: Record< string, string > = { };

    for ( const [ name, value ] of Object.entries( raw ) )
    {
        if ( !value )
        {
            missing.push( name );
            continue;
        }

        try
        {
            new URL( value );
        }
        catch
        {
            invalid.push( `${ name } ("${ value }")` );
            continue;
        }

        out[ name ] = value;
    }

    if ( missing.length > 0 || invalid.length > 0 )
    {
        const problems = [
            missing.length > 0 ? `missing: ${ missing.join( ', ' ) }` : null,
            invalid.length > 0 ? `not a valid URL: ${ invalid.join( ', ' ) }` : null
        ].filter( Boolean ).join( '; ' );

        throw new Error( `env.ts: invalid environment configuration - ${ problems }` );
    }

    return out;
}

const values = load( );

export const env =
{
    /** Public URL of this docs site, used for canonical, og:url and og:image. */
    docsUrl:     values.DOCS_URL.replace( /\/$/, '' ),
    /** Dashboard (frontend) URL, linked from the nav. */
    frontendUrl: values.FRONTEND_URL,
    /** Backend URL, linked from the nav. */
    backendUrl:  values.BACKEND_URL,
    /** OpenAPI schema the API reference pages are generated from. */
    openapiUrl:  values.OPENAPI_URL
};
