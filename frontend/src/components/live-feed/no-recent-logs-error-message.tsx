import { Link } from '@tanstack/react-router';
import { Card, CardDescription } from '../ui/card';

export function NoRecentLogsErrorMessage( )
{
    return (
        <Card variant='medium'>
            <CardDescription variant='medium'>
                No log entries yet. Send traffic to your ingest endpoint -{' '}
                <Link to="/settings" className="font-medium text-accent underline underline-offset-2 hover:text-accent-strong">
                    get your API key
                </Link>
                {' '}to start sending logs now.
            </CardDescription>
        </Card>
    );
}