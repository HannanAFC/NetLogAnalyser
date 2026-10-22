import { promisify } from 'node:util';
import { brotliCompress, constants, gzip } from 'node:zlib';
import { onResponse } from 'nitro/h3';

// Static assets are precompressed at build time, but SSR/prerendered HTML and the generated text endpoints are not.
const brotli = promisify( brotliCompress );
const gzipAsync = promisify( gzip );

const compressible = /^(text\/|application\/(json|xml|javascript))/;
const minBytes = 1024;

export default onResponse( async( response, event ) =>
{
    const type = response.headers.get( 'content-type' ) ?? '';
    if ( !response.body || response.status !== 200 || response.headers.has( 'content-encoding' ) || !compressible.test( type ) )
    {
        return;
    }

    const accepted = event.req.headers.get( 'accept-encoding' ) ?? '';
    const encoding = /\bbr\b/.test( accepted ) ? 'br' : /\bgzip\b/.test( accepted ) ? 'gzip' : null;

    const headers = new Headers( response.headers );
    headers.append( 'vary', 'Accept-Encoding' );

    if ( !encoding )
    {
        return new Response( response.body, { status: response.status, headers } );
    }

    const body = Buffer.from( await response.arrayBuffer( ) );
    if ( body.length < minBytes )
    {
        return new Response( body, { status: response.status, headers } );
    }

    const compressed = encoding === 'br'
        ? await brotli( body, { params: { [ constants.BROTLI_PARAM_QUALITY ]: 5 } } )
        : await gzipAsync( body );

    headers.set( 'content-encoding', encoding );
    headers.set( 'content-length', String( compressed.length ) );
    return new Response( compressed, { status: response.status, headers } );
} );
