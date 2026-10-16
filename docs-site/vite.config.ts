import react from '@vitejs/plugin-react';
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import { defineConfig, loadEnv } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { fumadocsMdx } from 'fumadocs-mdx/vite';
import { nitro } from 'nitro/vite';

// Public URLs consumed by src/lib/env.ts. Read from the process environment (Docker) or docs-site/.env, then
// inlined so the server render and the browser see identical values.
const envKeys = [ 'DOCS_URL', 'FRONTEND_URL', 'BACKEND_URL', 'OPENAPI_URL' ];

export default defineConfig( ( { mode } ) =>
{
  const fileEnv = loadEnv( mode, process.cwd( ), '' );
  const define = Object.fromEntries(
    envKeys.map( ( key ) => [ `process.env.${ key }`, JSON.stringify( process.env[ key ] ?? fileEnv[ key ] ?? '' ) ] )
  );

  return {
  define,
  server: {
    port: 3000
  },
  plugins: [
    fumadocsMdx(),
    tailwindcss(),
    tanstackStart( {
      prerender: {
        enabled: true
      }
    } ),
    react(),
    // please see https://tanstack.com/start/latest/docs/framework/react/guide/hosting#nitro for guides on hosting
    nitro( {
      preset: 'vercel'
    } )
  ],
  resolve: {
    tsconfigPaths: true,
    alias: {
      tslib: 'tslib/tslib.es6.js'
    }
  }
};
} );
