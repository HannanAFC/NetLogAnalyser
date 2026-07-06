import { devtools } from '@tanstack/devtools-vite';
import { defineConfig } from 'vite';

import { tanstackRouter } from '@tanstack/router-plugin/vite';

import tailwindcss from '@tailwindcss/vite';
import viteReact from '@vitejs/plugin-react';

export default defineConfig( ( { } ) =>
{
    return {
		resolve: { tsconfigPaths: true },
		plugins:
        [
			devtools( ),
			tailwindcss( ),
			tanstackRouter( { target: 'react', autoCodeSplitting: true } ),
			viteReact( ),
		],
        server:
        {
            host: true,
            port: 3000
        }
    };
} );