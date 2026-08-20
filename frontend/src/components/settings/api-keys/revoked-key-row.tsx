import { Card, CardTitle } from '#/components/ui/card';
import type { ApiKey } from '#/lib/api-keys/types';
import { formatApiKeyDate } from '#/lib/utils';

export function RevokedKeyRow( { apiKey }: { apiKey: ApiKey } )
{
    return (
        <Card variant='default' className='flex items-center rounded-md border border-border bg-inset px-4 py-3 opacity-60'>
            <div className='min-w-0 flex-1'>
                <CardTitle className='truncate'>
                    { apiKey.label }
                </CardTitle>
                <div className='mt-1 flex items-center gap-3 text-xs text-text-tertiary'>
                    <span className='font-mono'>{ apiKey.key_prefix }…</span>
                    <span>·</span>
                    <span>Created { formatApiKeyDate( apiKey.created_at ) }</span>
                    <span>·</span>
                    <span>Revoked { formatApiKeyDate( apiKey.revoked_at ) }</span>
                </div>
            </div>
        </Card>
    );
}