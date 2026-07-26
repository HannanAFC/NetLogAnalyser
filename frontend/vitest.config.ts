import { defineConfig } from 'vitest/config';

export default defineConfig(
{
	test:
	{
		projects:
		[
			{
				test:
				{
					name: 'unit',
					environment: 'jsdom',
					setupFiles: [ './test/setup.ts' ],
					include: [ 'src/**/*.test.{ts,tsx}' ],
					exclude: [ 'test/integration/**' ]
				}
			},
			{
				test:
				{
					name: 'integration',
					environment: 'node',
					include: [ 'test/integration/**/*.test.ts' ]
				}
			}
		]
	}
} );
