#!/usr/bin/env node
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

// dotenv is only relevant locally (reads frontend/.env). On Render and in
// Docker builds the real env vars are already present in process.env, so a
// missing dotenv package or missing .env file here is not an error.
try
{
	const dotenv = await import( 'dotenv' );
	dotenv.config( );
}
catch
{
	// no-op
}

const outFlagIndex = process.argv.indexOf( '--out' );
const outPath = outFlagIndex !== -1 ? process.argv[ outFlagIndex + 1 ] : 'public/config.js';

const required = [ 'API_BASE_URL', 'WS_BASE_URL' ];
const missing = required.filter( ( key ) => !process.env[ key ] );

if ( missing.length > 0 )
{
	console.error( `generate-config: missing required env vars: ${ missing.join( ', ' ) }` );
	process.exit( 1 );
}

const config =
{
	API_BASE_URL: process.env.API_BASE_URL,
	WS_BASE_URL:  process.env.WS_BASE_URL
};

mkdirSync( dirname( outPath ), { recursive: true } );
writeFileSync( outPath, `window.__ENV__ = ${ JSON.stringify( config, null, 2 ) };\n` );
console.log( `generate-config: wrote ${ outPath }` );
