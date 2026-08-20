import { logsSearchSchema } from '#/features/logs/schemas';
import { describe, expect, it } from 'vitest';

describe( 'logsSearchSchema', ( ) =>
{
	it( 'accepts a valid cursor string', ( ) =>
	{
		const result = logsSearchSchema.safeParse( { cursor: 'abc123' } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.cursor ).toBe( 'abc123' );
		}
	} );

	it( 'accepts an empty object (cursor is optional)', ( ) =>
	{
		const result = logsSearchSchema.safeParse( { } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.cursor ).toBeUndefined( );
		}
	} );

	it( 'rejects an empty cursor string', ( ) =>
	{
		const result = logsSearchSchema.safeParse( { cursor: '' } );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects a cursor that is not a string', ( ) =>
	{
		const result = logsSearchSchema.safeParse( { cursor: 123 } );

		expect( result.success ).toBe( false );
	} );

	it( 'strips unknown fields', ( ) =>
	{
		const result = logsSearchSchema.safeParse(
		{
			cursor:  'abc',
			unknown: 'field'
		} );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data ).not.toHaveProperty( 'unknown' );
		}
	} );
} );
