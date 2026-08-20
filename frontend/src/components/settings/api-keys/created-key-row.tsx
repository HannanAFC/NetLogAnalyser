import { Button } from '#/components/ui/button';
import { Card, CardDescription, CardLabel } from '#/components/ui/card';
import type { CreatedApiKey } from '#/lib/api-keys/types';
import { Check, Copy } from 'lucide-react';
import { useState } from 'react';

interface CreateKeyProps
{
    newKey: CreatedApiKey;
    setNewKey: ( apiKey: CreatedApiKey | null ) => void;
}

export function CreatedKeyRow( { newKey, setNewKey }: CreateKeyProps )
{
	const [ copied, setCopied ] = useState( false );

	function handleCopy( text: string )
	{
		navigator.clipboard.writeText( text );
		setCopied( true );
		setTimeout( ( ) => setCopied( false ), 2000 );
	}


	return (
		<Card variant="success" className="flex flex-col gap-4">
			<CardLabel variant="success">API key created</CardLabel>
			<CardDescription variant="success" className="font-bold">
				Copy this key now - it won't be shown again.
			</CardDescription>
			<div className="mt-2 flex items-center gap-2">
				<code className="flex-1 rounded-md border border-border bg-card px-3 py-2 font-mono text-xs text-text-primary break-all">
					{ newKey.api_key }
				</code>
				<Button
					variant='ghost'
					onClick={ ( ) => handleCopy( newKey.api_key ) }
				>
					{ copied
						? <Check className="h-4 w-4 text-success" />
						: <Copy className="h-4 w-4" />
					}
				</Button>
			</div>
			<Button
				onClick={ ( ) => setNewKey( null ) }
				variant='danger'
				size="sm"
				className="max-w-max"
			>
				Dismiss
			</Button>
		</Card>
	);
}