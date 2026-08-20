import { Button } from '#/components/ui/button';
import { Card, CardDescription } from '#/components/ui/card';
import { BodySm, BodyText, Heading } from '#/components/ui/heading';
import { Input, Label } from '#/components/ui/input';
import { useDeleteUser } from '#/features/users/hooks';
import { deleteUserSchema } from '#/features/users/schemas';
import { cn, fieldError } from '#/lib/utils';
import { useForm } from '@tanstack/react-form';
import type { HTMLAttributes } from 'react';

type ComponentCallback = ( ...args: any[ ] ) => void;

interface DeleteUserDialogueProps extends HTMLAttributes< HTMLDivElement >
{
    onConfirm: ComponentCallback;
    onCancel:  ComponentCallback;
}

export function DeleteUserDialogue( { className, onConfirm, onCancel, ...props }: DeleteUserDialogueProps )
{
    const deleteUser = useDeleteUser( );

    function onDialogueCancel( )
    {
        onCancel( );
    }

    const form = useForm(
    {
        defaultValues: { password: '', confirm_password: '' },
        onSubmit: async( { value } ) =>
        {
            try
            {
                const parsed = deleteUserSchema.parse( value );
                await deleteUser.mutateAsync( parsed );
                onConfirm( );
            }
            catch
            {
                // already handled
            }
        }
    } );

    return (
        <Card
            variant='critical'
            className={ cn( 'flex flex-col gap-4 bg-paper w-lg max-w-[calc(100vw-32px)]', className ) }
            { ...props }
        >
            <Heading
                level='h2'
                className='text-danger text-center'
            >
                Delete your account
            </Heading>
            <BodyText className='text-text-primary'>
                By deleting your account, all your data will be deleted, including any ingested logs and exports. This action is <strong>permanent</strong> and data cannot be recovered after your account is deleted.
            </BodyText>
            <form
                onSubmit={ ( event ) =>
                {
                    event.preventDefault( );
                    event.stopPropagation( );
                    form.handleSubmit( );
                }}
                className="space-y-4"
            >

                <form.Field
                    name="password"
                    validators={{ onChange: deleteUserSchema.shape.password, onBlur: deleteUserSchema.shape.password }}
                >
                    { ( field ) =>
                        (
                            <div>
                                <Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Password</Label>
                                <Input
                                    id={ field.name }
                                    type="password"
                                    autoComplete="password"
                                    value={ field.state.value }
                                    onBlur={ field.handleBlur }
                                    onChange={ ( e ) => field.handleChange( e.target.value ) }
                                    className='focus:border-danger focus:ring-danger/25'
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <BodySm className="text-critical">
                                        { fieldError( field.state.meta.errors ) }
                                    </BodySm>
                                )}
                            </div>
                        )}
                </form.Field>

                <form.Field
                    name="confirm_password"
                    validators={
                        {
                            onChange: ( { value, fieldApi } ) =>
                            {
                                if ( !value ) return 'Please confirm your password';
                                if ( value !== fieldApi.form.getFieldValue( 'password' ) ) return "Passwords don't match";
                                return undefined;
                            }
                        }}
                >
                    { ( field ) =>
                        (
                            <div>
                                <Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Confirm password</Label>
                                <Input
                                    id={ field.name }
                                    type="password"
                                    autoComplete="password"
                                    value={ field.state.value }
                                    onBlur={ field.handleBlur }
                                    onChange={ ( e ) => field.handleChange( e.target.value ) }
                                    className='focus:border-danger focus:ring-danger/25'
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <BodySm className="text-critical">
                                        { fieldError( field.state.meta.errors ) }
                                    </BodySm>
                                )}
                            </div>
                        )}
                </form.Field>

                <div className='grid grid-cols-2 gap-4'>
                    <form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
                        { ( [ canSubmit, isPristine ] ) =>
                            (
                                <Button
                                    type="submit"
                                    variant='danger'
                                    className='inline-flex itmes-center justify-center mt-auto'
                                    disabled={ !canSubmit || isPristine || deleteUser.isPending }
                                >
                                    { deleteUser.isPending ? 'Deleting account…' : 'Delete account' }
                                </Button>
                            )}
                    </form.Subscribe>
                    <Button
                        variant='secondary'
                        className='inline-flex itmes-center justify-center mt-auto'
                        onClick={ onDialogueCancel }
                    >
                        Cancel
                    </Button>
                </div>
            </form>
            { deleteUser.isSuccess &&
            (
                <Card variant='success'>
                    <CardDescription variant='success'>
                        You account has been deleted successfully. You will be redirected to the login page soon.
                    </CardDescription>
                </Card>
            ) };
        </Card>
    );
}