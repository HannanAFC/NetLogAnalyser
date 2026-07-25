import { Button } from '#/components/ui/button';
import { BodySm, BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { Input, Label } from '#/components/ui/input';
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '#/features/api-keys/hooks';
import { createApiKeySchema } from '#/features/api-keys/schemas';
import type { ApiKey, CreatedApiKey } from '#/lib/api-keys/types';
import { apiError } from '#/lib/api/errors';
import { useForm } from '@tanstack/react-form';
import { createFileRoute } from '@tanstack/react-router';
import { Ban, Check, Copy, Plus } from 'lucide-react';
import { useState } from 'react';

export const Route = createFileRoute( '/_authenticated/settings' )(
{
	component: SettingsPage,
	head: ( ) =>(
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/settings'
			}
		],
		meta:
		[
			{
				title: "Settings | NetLogAnalyser"
			},
			{
				name: 'description',
				content: 'Manage your NetLogAnalyser account - create, view and revoke API keys and edit account settings.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Settings'
			},
			{
				name: 'og:description',
				content: 'Manage your NetLogAnalyser account - create, view and revoke API keys and edit account settings.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Settings'
			},
			{
				name: 'twitter:description',
				content: 'Manage your NetLogAnalyser account - create, view and revoke API keys and edit account settings.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/settings'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/settings'
			}
		]
	} )
} );

function formatDate( iso: string | null ): string
{
	if ( !iso ) return '-';
	return new Intl.DateTimeFormat( 'en-US',
	{
		month: 'short',
		day: 'numeric',
		year: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	} ).format( new Date( iso ) );
}

interface CreateKeyProps
{
	newKey: CreatedApiKey;
	setNewKey: ( apiKey: CreatedApiKey | null ) => void;
}

function ApiKeyRow( { apiKey, onRevoke, isRevoking }: { apiKey: ApiKey; onRevoke: ( id: string ) => void; isRevoking: boolean } )
{
	return (
		<div className="flex items-center justify-between rounded-md border border-border bg-card px-4 py-3">
			<div className="min-w-0 flex-1">
				<div className="flex items-center gap-2">
					<span className="text-sm font-medium text-text-primary truncate">
						{ apiKey.label }
					</span>
				</div>
				<div className="mt-1 flex items-center gap-3 text-xs text-text-tertiary">
					<span>·</span>
					<span>Created { formatDate( apiKey.created_at ) }</span>
					{ apiKey.last_used_at && (
						<>
							<span>·</span>
							<span>Last used { formatDate( apiKey.last_used_at ) }</span>
						</>
					) }
				</div>
			</div>
			<Button
				variant='danger'
				size='sm'
				onClick={ () => onRevoke( apiKey.id ) }
				disabled={ isRevoking }
			>
				<Ban className="h-3 w-3" />
				Revoke
			</Button>
		</div>
	);
}

function RevokedKeyRow( { apiKey }: { apiKey: ApiKey } )
{
	return (
		<div className="flex items-center rounded-md border border-border bg-inset px-4 py-3 opacity-60">
			<div className="min-w-0 flex-1">
				<div className="flex items-center gap-2">
					<span className="text-sm font-medium text-text-secondary truncate">
						{ apiKey.label }
					</span>
				</div>
				<div className="mt-1 flex items-center gap-3 text-xs text-text-tertiary">
					<span className="font-mono">{ apiKey.key_prefix }…</span>
					<span>·</span>
					<span>Created { formatDate( apiKey.created_at ) }</span>
					<span>·</span>
					<span>Revoked { formatDate( apiKey.revoked_at ) }</span>
				</div>
			</div>
		</div>
	);
}

function CreatedKeyRow( { newKey, setNewKey }: CreateKeyProps )
{
	const [ copied, setCopied ] = useState( false );

	function handleCopy( text: string )
	{
		navigator.clipboard.writeText( text );
		setCopied( true );
		setTimeout( () => setCopied( false ), 2000 );
	}


	return (
		<div className="rounded-md border border-success bg-success/10 px-4 py-3">
			<Heading level="h3" className="text-success uppercase ">API key created</Heading>
			<BodySm>
				Copy this key now - it won't be shown again.
			</BodySm>
			<div className="mt-2 flex items-center gap-2">
				<code className="flex-1 rounded-md border border-border bg-card px-3 py-2 font-mono text-xs text-text-primary break-all">
					{ newKey.api_key }
				</code>
				<Button
					variant='ghost'
					onClick={ () => handleCopy( newKey.key_prefix ) }
				>
					{ copied
						? <Check className="h-4 w-4 text-success" />
						: <Copy className="h-4 w-4" />
					}
				</Button>
			</div>
			<Button
				onClick={ ( ) => setNewKey( null ) }
				variant='ghost'
			>
				Dismiss
			</Button>
		</div>
	);
}

function ApiKeysSection( )
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
							className="disabled:opacity-50 size-max mt-[20px]"
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

function SettingsPage( )
{

	return (
		<div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
			<div className="mb-8">
				<Eyebrow>Configuration</Eyebrow>
				<Heading level="h1" className="mt-1">Settings</Heading>
				<BodyText className="mt-2">Manage your account, API keys, and preferences.</BodyText>
			</div>

			<div className="mb-6 flex gap-1 border-b border-border">
				<button
					type="button"
					className="relative px-4 py-2.5 text-sm font-medium text-accent-strong after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px] after:rounded-full after:bg-accent"
				>
					API keys
				</button>
			</div>

			<ApiKeysSection />
		</div>
	);
}