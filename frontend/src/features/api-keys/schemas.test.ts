import { createApiKeySchema } from '#/features/api-keys/schemas';
import { describe, expect, it } from 'vitest';

describe( 'createApiKeySchema', ( ) =>
{
	it( 'accepts a valid label', ( ) =>
	{
		const result = createApiKeySchema.safeParse( { label: 'label' } );

		expect( result.success ).toBe( true );
	} );

	it( 'rejects an empty label', ( ) =>
	{
		const result = createApiKeySchema.safeParse( { label: '' } );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects a whitespace only label', ( ) =>
	{
		const result = createApiKeySchema.safeParse( { label: '   ' } );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects a label exceeding 100 characters', ( ) =>
	{
		const longLabel = 'a'.repeat( 101 ); // 101 chars
		const result    = createApiKeySchema.safeParse( { label: longLabel } );

		expect( result.success ).toBe( false );
	} );

	it( 'accepts a label at the 100-character boundary (valid email)', ( ) =>
	{
		const label  = 'a'.repeat( 100 );
		const result = createApiKeySchema.safeParse( { label } );

		expect( result.success ).toBe( true );
	} );
} );
