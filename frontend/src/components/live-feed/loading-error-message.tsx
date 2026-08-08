import { Card, CardDescription } from '../ui/card';

export function LoadingErrorMessage( )
{
    return (
        <Card variant='critical'>
            <CardDescription variant='critical'>
            Couldn't load recent logs. The live feed will still start once connected.
            </CardDescription>
        </Card>
    );
}