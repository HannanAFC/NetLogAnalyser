import { Card, CardDescription } from '../ui/card';

export function LoadingErrorMessage( )
{
    return (
        <Card variant='critical'>
            <CardDescription variant='critical'>
                Couldn't load log history, please try again.
            </CardDescription>
        </Card>
    );
}