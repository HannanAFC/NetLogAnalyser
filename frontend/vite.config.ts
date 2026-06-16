import { devtools } from '@tanstack/devtools-vite';
import { defineConfig, loadEnv } from 'vite';

import { tanstackRouter } from '@tanstack/router-plugin/vite';

import tailwindcss from '@tailwindcss/vite';
import viteReact from '@vitejs/plugin-react';

export default defineConfig( ( { mode } ) =>
{
    const env = loadEnv( mode, process.cwd( ), '' );

    return {
		resolve: { tsconfigPaths: true },
		plugins: [
			devtools( ),
			tailwindcss( ),
			tanstackRouter( { target: 'react', autoCodeSplitting: true } ),
			viteReact( ),
		],
        server:
        {
            host: true,
            port: 3000,
            proxy:
            {
                '/api':
                {
                    target: env.VITE_API_BASE_URL || 'http://localhost:8000',
                    changeOrigin: true,
                    rewrite: ( path ) => path.replace( /^\/api/, '' )
                },
                '/ws':
                {
                    target: env.VITE_WS_BASE_URL || 'ws://localhost:8000ws',
                    ws: true
                }
            }
        }
    };
} );