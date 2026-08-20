import z from 'zod';
import { displayNameSchema, emailSchema, passwordSchema } from '../auth/schemas';

export const changeUserPasswordSchema = z
    .object(
    {
        current_password: z.string( ),
        password:         passwordSchema,
        confirm_password: z.string( )

    } )
    .refine ( ( data ) => data.password === data.confirm_password,
	{
		message: "Passwords don't match",
		path: [ 'confirm_password' ]
	} );
export type ChangeUserPasswordPayload = z.infer< typeof changeUserPasswordSchema >;

export const changeUserDetailsSchema = z
    .object(
    {
        email:        emailSchema.nullable( ),
        display_name: displayNameSchema.nullable( )
    } );
export type ChangeUserDetailsPayload = z.infer< typeof changeUserDetailsSchema >;

export const deleteUserSchema = z
    .object(
    {
        password:         z.string( ),
        confirm_password: z.string( )

    } )
    .refine ( ( data ) => data.password === data.confirm_password,
	{
		message: "Passwords don't match",
		path: [ 'confirm_password' ]
	} );

export type DeleteUserPayload = z.infer< typeof deleteUserSchema >;