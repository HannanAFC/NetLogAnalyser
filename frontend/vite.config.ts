import { devtools } from '@tanstack/devtools-vite';
import { defineConfig } from 'vite';

import { tanstackRouter } from '@tanstack/router-plugin/vite';

import tailwindcss from '@tailwindcss/vite';
import viteReact from '@vitejs/plugin-react';
import type { Plugin } from 'vite';

/**
 * Preload the Inter latin subset.
 */
function preloadInterFont( ): Plugin
{
	return {
		name:  'preload-inter-font',
		apply: 'build',
		transformIndexHtml:
		{
			order:   'post',
			handler: ( _html, ctx ) =>
			{
				const font = Object.keys( ctx.bundle ?? { } )
					.find( ( file ) => /inter-latin-wght-normal.*\.woff2$/.test( file ) );

				if ( !font ) return [ ];

				return [
                    {
                        tag:   'link',
                        attrs: { rel: 'preload', as: 'font', type: 'font/woff2', crossorigin: '', href: `/${ font }` },
                        injectTo: 'head-prepend'
                    }
                ];
			}
		}
	};
}

const FRONTEND_PORT = Number( process.env.FRONTEND_PORT ) || 3000;

export default defineConfig( ( ) =>
{
	return {
		resolve: { tsconfigPaths: true },
		plugins:
        [
        	devtools( ),
        	tailwindcss( ),
        	tanstackRouter( { target: 'react', autoCodeSplitting: true } ),
        	viteReact( ),
        	preloadInterFont( )
        ],
		server:
        {
			port: FRONTEND_PORT,
    		strictPort: true
        },
		hmr:
		{
			clientPort: FRONTEND_PORT
		}
	};
} );
