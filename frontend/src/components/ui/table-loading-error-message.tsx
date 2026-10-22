import { Card, CardDescription } from '../ui/card';
import type { HTMLAttributes, ReactNode } from 'react';

export interface TableLoadingErrorMessageProps extends HTMLAttributes< HTMLDivElement >
{
    children: ReactNode
}

export function TableLoadingErrorMessage( { children }: TableLoadingErrorMessageProps )
{
    return (
        <Card variant='critical'>
            <CardDescription variant='critical'>
                { children }
            </CardDescription>
        </Card>
    );
}