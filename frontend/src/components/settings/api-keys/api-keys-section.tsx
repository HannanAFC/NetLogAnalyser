import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '#/features/api-keys/hooks';
import { createApiKeySchema } from '#/features/api-keys/schemas';
import type { CreatedApiKey } from '#/lib/api-keys/types';
import { useForm } from '@tanstack/react-form';
import { useState } from 'react';
import { CreatedKeyRow } from './created-key-row';
import { Input, Label } from '#/components/ui/input';
import { BodySm } from '#/components/ui/heading';
import { Button } from '#/components/ui/button';
import { Plus } from 'lucide-react';
import { apiError } from '#/lib/api/errors';
import { ApiKeyRow } from './api-key-row';
import { RevokedKeyRow } from './revoked-key-row';

export function ApiKeysSection( )
{
	const { data: apiKeys, isLoading } = useApiKeys( );
	const createApiKey = useCreateApiKey( );
	const revokeApiKey = useRevokeApiKey( );
	const [ newKey, setNewKey ] = useState< CreatedApiKey | null >( null );

	const form = useForm(
		{
			defaultValues: { label: '' },
			onSubmit: async( { value } ) =>
			{
				const result = await createApiKey.mutateAsync( createApiKeySchema.parse( value ) );
				setNewKey( result );
				form.reset();
			}
		} );

	const activeKeys = apiKeys?.filter( ( k ) => !k.revoked_at ) ?? [ ];
	const revokedKeys = apiKeys?.filter( ( k ) => k.revoked_at ) ?? [ ];

	if ( isLoading )
	{
		return (
			<div className="flex items-center gap-2 py-8 text-sm text-text-tertiary">
				<div className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-accent" />
				Loading API keys…
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{ newKey && (
				<CreatedKeyRow newKey={ newKey } setNewKey={ setNewKey } />
			)}

			<form
				onSubmit={ ( e ) =>
				{
					e.preventDefault( );
					e.stopPropagation( );
					form.handleSubmit( );
				} }
				className="flex gap-3"
			>
				<form.Field
					name="label"
					validators={ { onChange: createApiKeySchema.shape.label, onBlur: createApiKeySchema.shape.label } }
				>
					{ ( field ) =>
					(
						<div className="flex-1">
							<Label htmlFor={ field.name } size="xs">New key label</Label>
							<Input
								id={ field.name }
								type="text"
								placeholder="e.g. Production ingest"
								value={ field.state.value }
								onBlur={ field.handleBlur }
								onChange={ ( e ) => field.handleChange( e.target.value ) }
							/>
							{ field.state.meta.errors.length > 0 && (
								<BodySm className="text-critical">
									{ typeof field.state.meta.errors[ 0 ] === 'string'
										? field.state.meta.errors[ 0 ]
									: ( field.state.meta.errors[ 0 ] as { message: string } ).message }
								</BodySm>
							)}
						</div>
					) }
				</form.Field>
				<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
					{ ( [ canSubmit, isPristine ] ) => (
						<Button
							type="submit"
							disabled={ !canSubmit || isPristine || createApiKey.isPending }
							className="disabled:opacity-50 size-max mt-5"
							variant='primary'
						>
							<Plus className="h-3.5 w-3.5" />
							{ createApiKey.isPending ? 'Creating…' : 'Create key' }
						</Button>
					) }
				</form.Subscribe>
			</form>

			{ createApiKey.isError && (
				<BodySm className="text-critical">
					{ apiError( createApiKey.error ) ?? 'Failed to create API key.' }
				</BodySm>
			) }

			{ activeKeys.length > 0 && (
				<div>
					<BodySm className="mb-2 font-semibold uppercase tracking-[0.08em] text-text-tertiary">
						Active keys ({ activeKeys.length })
					</BodySm>
					<div className="space-y-2">
						{ activeKeys.map( ( key ) =>
							(
								<ApiKeyRow
									key={ key.id }
									apiKey={ key }
									onRevoke={ ( id ) => revokeApiKey.mutate( id ) }
									isRevoking={ revokeApiKey.isPending && revokeApiKey.variables === key.id }
								/>
							) ) }
					</div>
				</div>
			) }

			{ activeKeys.length === 0 && !createApiKey.isPending && (
				<BodySm className="py-4 text-text-tertiary">
					No active API keys. Create one above to start sending data.
				</BodySm>
			) }

			{ revokedKeys.length > 0 && (
				<div>
					<BodySm className="mb-2 font-semibold uppercase tracking-[0.08em] text-text-tertiary">
						Revoked keys ({ revokedKeys.length })
					</BodySm>
					<div className="space-y-2">
						{ revokedKeys.map( ( key ) =>
							(
								<RevokedKeyRow key={ key.id } apiKey={ key } />
							) ) }
					</div>
				</div>
			) }
		</div>
	);
}