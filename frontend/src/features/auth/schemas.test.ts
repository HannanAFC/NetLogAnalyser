import { forgotPasswordSchema, loginSchema, registerSchema, resendVerificationSchema, resetPasswordSchema } from '#/features/auth/schemas';
import { describe, expect, it } from 'vitest';

describe( 'loginSchema', ( ) =>
{
	it( 'accepts a valid email and non-empty password', ( ) =>
	{
		const result = loginSchema.safeParse(
		{
			email: 'jane@example.com',
			password: 'Str0ngP@ss'
		} );

		expect( result.success ).toBe( true );
	} );

	it( 'rejects an invalid email', ( ) =>
	{
		const result = loginSchema.safeParse(
		{
			email: 'not-an-email',
			password: 'anything'
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects an empty password', ( ) =>
	{
		const result = loginSchema.safeParse( { email: 'jane@example.com', password: '' } );

		expect( result.success ).toBe( false );
	} );
} );

describe( 'registerSchema', ( ) =>
{
	it( 'accepts a valid email, non-empty display name and non-empty password', ( ) =>
	{
		const result = registerSchema.safeParse(
		{
			email: 'jane@example.com',
			display_name: 'jane',
			password: 'Str0ngP@ss',
			confirm_password: 'Str0ngP@ss'
		} );

		expect( result.success ).toBe( true );
	} );

	it( 'rejects an invalid email', ( ) =>
	{
		const result = loginSchema.safeParse(
		{
			email: 'not-an-email',
			display_name: 'jane',
			password: 'Str0ngP@ss',
			confirm_password: 'Str0ngP@ss'
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects an empty display name', ( ) =>
	{
		const result = loginSchema.safeParse(
		{
			email: 'not-an-email',
			display_name: '',
			password: 'Str0ngP@ss',
			confirm_password: 'Str0ngP@ss'
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects an empty password', ( ) =>
	{
		const result = loginSchema.safeParse(
		{
			email: 'not-an-email',
			display_name: 'jane',
			password: '',
			confirm_password: ''
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects mismatched passwords', ( ) =>
	{
		const result = loginSchema.safeParse(
		{
			email: 'not-an-email',
			display_name: 'jane',
			password: 'Str0ngP@ss',
			confirm_password: 'different'
		} );

		expect( result.success ).toBe( false );
	} );
} );


describe( 'forgotPasswordSchema', ( ) =>
{
	it( 'accepts a valid email', ( ) =>
	{
		const result = forgotPasswordSchema.safeParse( { email: 'jane@example.com' } );

		expect( result.success ).toBe( true );
	} );

	it( 'rejects an invalid email', ( ) =>
	{
		const result = forgotPasswordSchema.safeParse( { email: 'not-an-email' } );

		expect( result.success ).toBe( false );
	} );
} );

describe( 'resetPasswordSchema', ( ) =>
{
	it( 'accepts a token and a password of at least 8 characters', ( ) =>
	{
		const result = resetPasswordSchema.safeParse(
		{
			token: 'some-token',
			password: 'Str0ngP@ss',
			confirm_password: 'Str0ngP@ss'
		} );

		expect( result.success ).toBe( true );
	} );

	it( 'rejects a password under 8 characters', ( ) =>
	{
		const result = resetPasswordSchema.safeParse(
		{
			token: 'some-token',
			password: 'Strong@',
			confirm_password: 'Strong@'
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects mismatched passwords', ( ) =>
	{
		const result = resetPasswordSchema.safeParse(
		{
			email: 'not-an-email',
			display_name: 'jane',
			password: 'Str0ngP@ss',
			confirm_password: 'different'
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects an empty token', ( ) =>
	{
		const result = resetPasswordSchema.safeParse( { token: '', password: 'longenough' } );

		expect( result.success ).toBe( false );
	} );
} );

describe( 'resendVerificationSchema', ( ) =>
{
	it( 'accepts a valid email', ( ) =>
	{
		const result = resendVerificationSchema.safeParse( { email: 'jane@example.com' } );

		expect( result.success ).toBe( true );
	} );

	it( 'rejects an invalid email', ( ) =>
	{
		const result = resendVerificationSchema.safeParse( { email: 'not-an-email' } );

		expect( result.success ).toBe( false );
	} );
} );