import { devtools } from '@tanstack/devtools-vite';
import { defineConfig } from 'vite';

import { tanstackRouter } from '@tanstack/router-plugin/vite';

import tailwindcss from '@tailwindcss/vite';
import viteReact from '@vitejs/plugin-react';

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
        	viteReact( )
        ],
		server:
        {
        	host: true,
			port: FRONTEND_PORT,
    		strictPort: true
        },
		hmr:
		{
			clientPort: FRONTEND_PORT
		}
	};
} );
