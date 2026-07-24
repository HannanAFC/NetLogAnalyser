import { z } from 'zod';

export const loginSchema = z.object(
{
	email:    z.email( 'Enter a valid email address' ),
	password: z.string( ).min( 1, 'Password is required' )
} );
export type LoginPayload = z.infer< typeof loginSchema >;

// Mirrors the backend's password_policy -
// keep the two in sync if that policy changes.
export const registerSchema = z
	.object(
	{
		email:            z.email( 'Enter a valid email address' ).max( 255, 'Email must be a maximum of 255 characters long' ),
		display_name:     z.string( ).min( 1, 'Display name is required' ).max( 50, 'Display name must be a maximum of 50 characters long' ),
		password:         z.string( ).min( 8, 'Password must be at least 8 characters' ),
		confirm_password: z.string( )
	} )
	.refine ( ( data ) => data.password === data.confirm_password,
	{
		message: "Passwords don't match",
		path: [ 'confirm_password' ]
	} );
export type RegisterPayload = z.infer< typeof registerSchema >;
export type RegisterRequestBody = Omit< RegisterPayload, 'confirm_password' >;

export const forgotPasswordSchema = z.object(
{
	email: z.email( 'Enter a valid email address' )
} );
export type ForgotPasswordPayload = z.infer< typeof forgotPasswordSchema >;

export const resetPasswordSchema = z.object(
{
	token:            z.string( ).min( 1 ),
	password:         z.string( ).min( 8, 'Password must be at least 8 characters' ),
	confirm_password: z.string( )
} );
export type ResetPasswordPayload = z.infer< typeof resetPasswordSchema >;
export type ResetPasswordRequestBody = Omit< ResetPasswordPayload, 'confirm_password' >;

export const resendVerificationSchema = z.object(
{
	email: z.email( 'Enter a valid email address' )
} );
export type ResendVerificationPayload = z.infer< typeof resendVerificationSchema >;