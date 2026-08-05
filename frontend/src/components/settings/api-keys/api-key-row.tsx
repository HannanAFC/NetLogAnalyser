import { Button } from "#/components/ui/button";
import { Card, CardTitle } from "#/components/ui/card";
import type { ApiKey } from "#/lib/api-keys/types";
import { formatApiKeyDate } from "#/lib/utils";
import { Ban } from "lucide-react";

export function ApiKeyRow( { apiKey, onRevoke, isRevoking }: { apiKey: ApiKey; onRevoke: ( id: string ) => void; isRevoking: boolean } )
{
    return (
        <Card className="flex items-center justify-between rounded-md border border-border bg-card px-4 py-3">
            <div className="min-w-0 flex-1">
                <CardTitle className="truncate">
                    { apiKey.label }
                </CardTitle>
                <div className="mt-1 flex items-center gap-3 text-xs text-text-tertiary">
                    <span className='font-mono'>{ apiKey.key_prefix }…</span>
                    <span>·</span>
                    <span>Created { formatApiKeyDate( apiKey.created_at ) }</span>
                    { apiKey.last_used_at && (
                        <>
                            <span>·</span>
                            <span>Last used { formatApiKeyDate( apiKey.last_used_at ) }</span>
                        </>
                    ) }
                </div>
            </div>
            <Button
                variant='danger'
                size='sm'
                onClick={ ( ) => onRevoke( apiKey.id ) }
                disabled={ isRevoking }
            >
                <Ban className="h-3 w-3" />
                Revoke
            </Button>
        </Card>
    );
}