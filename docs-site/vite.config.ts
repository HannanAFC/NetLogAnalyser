import react from '@vitejs/plugin-react';
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import { defineConfig, loadEnv } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { fumadocsMdx } from 'fumadocs-mdx/vite';
import { nitro } from 'nitro/vite';

const envKeys = [ 'DOCS_URL', 'FRONTEND_URL', 'BACKEND_URL', 'OPENAPI_URL' ];

export default defineConfig( ( { mode } ) =>
    {
        const fileEnv = loadEnv( mode, process.cwd( ), '' );
        const define  = Object.fromEntries(
            envKeys.map( ( key ) => [ `process.env.${ key }`, JSON.stringify( process.env[ key ] ?? fileEnv[ key ] ?? '' ) ] )
        );

        return {
            define,
            server:
            {
                port: 3000
            },
            preview:
            {
                host: '127.0.0.1'
            },
            plugins:
            [
                fumadocsMdx( ),
                tailwindcss( ),
                tanstackStart(
                    {
                        prerender:
                        {
                            enabled: true,
                            crawlLinks: true
                        },
                        sitemap:
                        {
                            enabled: true,
                            host: process.env.DOCS_URL || 'https://docs.netloganalyser.com'
                        }
                    } ),
                react(),
                // please see https://tanstack.com/start/latest/docs/framework/react/guide/hosting#nitro for guides on hosting
                nitro(
                    {
                        // Precompress static assets (gzip + brotli) at build time; src/server/compress.ts handles HTML at runtime
                        compressPublicAssets: true,
                        handlers: [ { route: '/**', middleware: true, handler: './src/server/compress.ts' } ],
                        routeRules:
                        {
                            // Screenshot filenames include a content hash (scripts/optimize-images.ts)
                            '/screenshots/**': { headers: { 'cache-control': 'public, max-age=31536000, immutable' } },
                            '/favicon*': { headers: { 'cache-control': 'public, max-age=604800' } },
                            '/apple-touch-icon.png': { headers: { 'cache-control': 'public, max-age=604800' } },
                            '/web-app-manifest-*': { headers: { 'cache-control': 'public, max-age=604800' } }
                        }
                    } )
            ],
            resolve:
            {
                tsconfigPaths: true,
                alias:
                {
                    tslib: 'tslib/tslib.es6.js'
                }
            }
        };
    } );
