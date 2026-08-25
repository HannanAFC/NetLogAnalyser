//  @ts-check

import { tanstackConfig } from '@tanstack/eslint-config'
import stylistic from '@stylistic/eslint-plugin'

export default [
	...tanstackConfig,
	{
		rules:
		{
			'import/no-cycle': 'off',
			'import/order': 'off',
			'sort-imports': 'off',
			'@typescript-eslint/array-type': 'off',
			'@typescript-eslint/require-await': 'off',
			'pnpm/json-enforce-catalog': 'off'
		}
	},
	{
		ignores: [ 'eslint.config.js', 'public/**' ]
	},
	{
		plugins:
		{
			'@stylistic': stylistic
		},
		rules:
		{
			'@stylistic/semi': [ 'error', 'always' ],
			'@stylistic/quotes': [ 'error', 'single', { avoidEscape: true } ],
			'@stylistic/comma-dangle': [ 'error', 'never' ],
			'@stylistic/space-in-parens': [ 'error', 'always' ],
			'@stylistic/array-bracket-spacing': [ 'error', 'always' ],
			'@stylistic/object-curly-spacing': [ 'error', 'always' ],
			'@stylistic/block-spacing': [ 'error', 'always' ],
			'@stylistic/template-curly-spacing': [ 'error', 'always' ],
			'@stylistic/computed-property-spacing': ['error', 'always' ],
			'@stylistic/keyword-spacing': [ 'error', { before: true, after: true } ],
			'@stylistic/space-before-function-paren': [ 'error', 'never' ],
			'@stylistic/space-before-blocks': [ 'error', 'always'],
			'@stylistic/brace-style': [ 'error', 'allman' ],
			'@stylistic/arrow-spacing': [ 'error', { before: true, after: true } ],
			'@stylistic/no-trailing-spaces': 'error',
			'@stylistic/type-annotation-spacing': 'error',
			'@stylistic/comma-spacing': [ 'error', { before: false, after: true } ]
		}
	}
]
