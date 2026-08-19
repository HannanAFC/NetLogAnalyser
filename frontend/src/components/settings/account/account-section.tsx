import { Button } from '#/components/ui/button';
import { Card, CardDescription, CardLabel } from '#/components/ui/card';
import { BodySm, Heading } from '#/components/ui/heading';
import { Input, Label } from '#/components/ui/input';
import { useLogout, useSession } from '#/features/auth/hooks';
import { useChangeUserDetails, useChangeUserPassword } from '#/features/users/hooks';
import { changeUserDetailsSchema, changeUserPasswordSchema } from '#/features/users/schemas';
import type { ChangeUserDetailsPayload, ChangeUserPasswordPayload } from '#/features/users/schemas';
import { apiError } from '#/lib/api/errors';
import { cn, fieldError } from '#/lib/utils';
import type { SettingsSectionProps } from '#/routes/_authenticated/settings';
import { useForm } from '@tanstack/react-form';
import { useOverlay } from '#/lib/overlay/overlay-context';
import { DeleteUserDialogue } from './delete-user-dialogue';

export function AccountSection( { className }: SettingsSectionProps )
{
    const { data: session }  = useSession( );
    const changeUserDetails  = useChangeUserDetails( );
    const changeUserPassword = useChangeUserPassword( );
    const logout             = useLogout( );
    const { open, close }    = useOverlay( );

    const form = useForm(
    {
        defaultValues:
        {
            email:        session ? session.email : null,
            display_name: session ? session.display_name : null
        } satisfies ChangeUserDetailsPayload,
        onSubmit: async( { value } ) =>
        {
            try
            {
                const payload =
                {
                    email: form.getFieldMeta( 'email' )?.isDirty && form.state.values.email !== session?.email
                    ? value.email || null
                    : null,

                    display_name: form.getFieldMeta( 'display_name' )?.isDirty
                    ? value.display_name || null
                    : null
                };

                await changeUserDetails.mutateAsync( payload );
            }
            catch
            {
                // handled by form
            }
        }
    } );

    const passwordForm = useForm(
    {
        defaultValues:
        {
            current_password: '',
            password:         '',
            confirm_password: ''
        } satisfies ChangeUserPasswordPayload,
        onSubmit: async( { value } ) =>
        {
            try
            {
                const parsed = changeUserPasswordSchema.parse( value );
                await changeUserPassword.mutateAsync( parsed );
            }
            catch
            {
                // handled by form
            }
        }
    } );

    function handleOpenDeleteMenu( )
    {
        const id = open
        (
            <DeleteUserDialogue
                onConfirm={ ( ) => undefined }
                onCancel={ ( ) => close( id ) }
            />
		);
    }

    return (
        <div className= { cn( 'space-y-6 flex flex-col md:grid md:grid-cols-2 gap-4 md:gap-8', className ) }>
            <Card className='flex flex-col gap-4'>
                <Heading level='h2'>
                    Account
                </Heading>
                <form
                    onSubmit={ ( event ) =>
                    {
                        event.preventDefault( );
                        event.stopPropagation( );
                        form.handleSubmit( );
                    } }
                    className='flex flex-col gap-4 grow'
                >
                    <form.Field
                        name='email'
                        validators={ { onChange: changeUserDetailsSchema.shape.email, onBlur: changeUserDetailsSchema.shape.email } }
                    >
                        { ( field ) =>
                        (
                            <div className='flex flex-col gap-2'>
                                <Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Email</Label>
                                <Input
                                    id={ field.name }
                                    type="email"
                                    autoComplete="email"
                                    value={ field.state.value ?? '' }
                                    onBlur={ field.handleBlur }
                                    onChange={ ( e ) => field.handleChange( e.target.value ) }
                                    className='bg-paper-2'
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <BodySm className="text-critical">
                                        { fieldError( field.state.meta.errors ) }
                                    </BodySm>
                                )}
                            </div>
                        ) }
                    </form.Field>

                    <form.Field
                        name="display_name"
                        validators={{ onChange: changeUserDetailsSchema.shape.display_name, onBlur: changeUserDetailsSchema.shape.display_name }}
                    >
                        { ( field ) =>
                        (
                            <div className='flex flex-col gap-2'>
                                <Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Display name</Label>
                                <Input
                                    id={ field.name }
                                    type="text"
                                    autoComplete="username"
                                    value={ field.state.value ?? '' }
                                    onBlur={ field.handleBlur }
                                    onChange={ ( e ) => field.handleChange( e.target.value ) }
                                    className='bg-paper-2'
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <BodySm className="text-critical">
                                        { fieldError( field.state.meta.errors ) }
                                    </BodySm>
                                )}
                            </div>
                        )}
                    </form.Field>

                    <form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
                        { ( [ canSubmit, isPristine ] ) =>
                        (
                            <Button
                                type="submit"
                                disabled={ !canSubmit || isPristine || changeUserDetails.isPending }
                                className='inline-flex itmes-center justify-center mt-auto'
                            >
                                { changeUserDetails.isPending ? 'Saving…' : 'Save' }
                            </Button>
                        )}
                    </form.Subscribe>
                    { changeUserDetails.isError &&
                    (
                        <Card variant='critical'>
                            <CardDescription variant='critical'>
                                { apiError( changeUserDetails.error ) ?? "Couldn't update account details." }
                            </CardDescription>
                        </Card>
                    ) }
                    { changeUserDetails.isSuccess &&
                    (
                        <Card variant='success'>
                            <CardDescription variant='success'>
                                { form.state.values.email !== session?.email ?
                                (
                                    <>A confirmation email has been sent to you.</>
                                ) :
                                (
                                    <>Account details updated successfully.</>
                                ) }
                            </CardDescription>
                        </Card>
                    ) }
                </form>
            </Card>
            <Card className='flex flex-col gap-4'>
                <Heading level='h2'>
                    Security
                </Heading>
                <form
                    onSubmit={ ( event ) =>
                    {
                        event.preventDefault( );
                        event.stopPropagation( );
                        passwordForm.handleSubmit( );
                    } }
                    className='flex flex-col gap-4'
                >
                    <passwordForm.Field
                        name="current_password"
                        validators={{ onChange: changeUserPasswordSchema.shape.current_password, onBlur: changeUserPasswordSchema.shape.current_password }}
                    >
                        { ( field ) =>
                        (
                            <div>
                                <Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Current password</Label>
                                <Input
                                    id={ field.name }
                                    type="password"
                                    autoComplete="password"
                                    value={ field.state.value }
                                    onBlur={ field.handleBlur }
                                    onChange={ ( e ) => field.handleChange( e.target.value ) }
                                    className='bg-paper-2'
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <BodySm className="text-critical">
                                        { fieldError( field.state.meta.errors ) }
                                    </BodySm>
                                )}
                            </div>
                        )}
                    </passwordForm.Field>

                    <passwordForm.Field
                        name="password"
                        validators={{ onChange: changeUserPasswordSchema.shape.password, onBlur: changeUserPasswordSchema.shape.password }}
                    >
                        { ( field ) =>
                        (
                            <div>
                                <Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">New password</Label>
                                <Input
                                    id={ field.name }
                                    type="password"
                                    autoComplete="new-password"
                                    value={ field.state.value }
                                    onBlur={ field.handleBlur }
                                    onChange={ ( e ) => field.handleChange( e.target.value ) }
                                    className='bg-paper-2'
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <BodySm className="text-critical">
                                        { fieldError( field.state.meta.errors ) }
                                    </BodySm>
                                )}
                            </div>
                        )}
                    </passwordForm.Field>

                    <passwordForm.Field
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
                                <Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Confirm new password</Label>
                                <Input
                                    id={ field.name }
                                    type="password"
                                    autoComplete="new-password"
                                    value={ field.state.value}
                                    onBlur={ field.handleBlur }
                                    onChange={ ( e ) => field.handleChange( e.target.value ) }
                                    className='bg-paper-2'
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <BodySm className="text-critical">
                                        { fieldError( field.state.meta.errors ) }
                                    </BodySm>
                                )}
                            </div>
                        )}
                    </passwordForm.Field>

                    <passwordForm.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
                        { ( [ canSubmit, isPristine ] ) =>
                        (
                            <Button
                                type="submit"
                                disabled={ !canSubmit || isPristine || changeUserPassword.isPending }
                                className='inline-flex itmes-center justify-center mt-auto'
                            >
                                { changeUserPassword.isPending ? 'Saving…' : 'Save' }
                            </Button>
                        )}
                    </passwordForm.Subscribe>
                    { changeUserPassword.isError &&
                    (
                        <Card variant='critical'>
                            <CardDescription variant='critical'>
                                { apiError( changeUserPassword.error ) ?? "Couldn't update account details." }
                            </CardDescription>
                        </Card>
                    ) }
                    { changeUserPassword.isSuccess &&
                    (
                        <Card variant='success'>
                            <CardDescription variant='success'>
                                { changeUserPassword.data.detail }
                            </CardDescription>
                        </Card>
                    ) }
                </form>
            </Card>
            <Card
                className='flex-col flex gap-4 h-full grow'
            >
                <Heading level='h2'>
                    Session controls
                </Heading>
                <CardLabel variant='default'>End session</CardLabel>
                <Button
                    size='sm'
                    className='inline-flex itmes-center justify-center mt-auto'
                    onClick={ ( ) => logout.mutateAsync( ) }
                >
                    Logout
                </Button>
            </Card>
            <Card
                variant='critical'
                className='flex-col flex gap-4'
            >
                <Heading level='h2'>
                    Danger zone
                </Heading>
                <CardLabel variant='critical'>Delete account</CardLabel>
                <Button
                    variant='danger'
                    size='sm'
                    className='inline-flex itmes-center justify-center mt-auto'
                    onClick={ handleOpenDeleteMenu }
                >
                    Delete
                </Button>
            </Card>;
        </div>
    );
}