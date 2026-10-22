#!/usr/bin/env node
// Prerenders the public routes into static HTML after `vite build` and the SSR
// build (dist-ssr/entry-server.js). The empty SPA shell is kept as
// dist/shell.html and serves as the fallback for every route that isn't
// prerendered, so e.g. /dashboard never flashes the landing page.
import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const ROUTES = [ '/', '/login', '/register', '/forgot-password', '/legal', '/legal/privacy-policy', '/legal/terms' ];

const distDir = resolve( 'dist' );
const ssrDir  = resolve( 'dist-ssr' );

const { render } = await import( pathToFileURL( join( ssrDir, 'entry-server.js' ) ).href );

const template = readFileSync( join( distDir, 'index.html' ), 'utf8' );
copyFileSync( join( distDir, 'index.html' ), join( distDir, 'shell.html' ) );

// React renders <title>/<meta>/<link> inline where <HeadContent /> sits (the
// start of the markup). Move that leading run into <head>; React adopts the
// matching head elements when the client hydrates.
const HEAD_TAGS = /^(?:<title>.*?<\/title>|<(?:meta|link)\b[^>]*\/?>)+/s;

for ( const url of ROUTES )
{
	const { html, pathname } = await render( url );

	if ( pathname !== url )
	{
		throw new Error( `prerender: ${ url } redirected to ${ pathname }` );
	}

	const leading  = html.match( HEAD_TAGS )?.[ 0 ] ?? '';
	const body     = html.slice( leading.length );
	// Tagged so main.tsx can drop them before hydrating; React doesn't adopt
	// them, and a leftover <title> would go stale after client navigation.
	const headTags = leading.replace( /<(title|meta|link)\b/g, '<$1 data-prerender' );

	if ( !body.includes( '<' ) )
	{
		throw new Error( `prerender: ${ url } rendered no markup` );
	}

	const page = template
		.replace( '</head>', `${ headTags }\n  </head>` )
		.replace( '<div id="app"></div>', `<div id="app">${ body }</div>` );

	const outFile = url === '/' ? join( distDir, 'index.html' ) : join( distDir, url, 'index.html' );
	mkdirSync( dirname( outFile ), { recursive: true } );
	writeFileSync( outFile, page );
	console.log( `prerendered ${ url } -> ${ outFile.replace( `${ distDir }/`, 'dist/' ) }` );
}

rmSync( ssrDir, { recursive: true, force: true } );
