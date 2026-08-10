import type { HTMLAttributes, ReactNode } from 'react';
import { Card, CardDescription } from './card';

export interface TableNoRecentsErrorMessageProps extends HTMLAttributes< HTMLDivElement >
{
    children: ReactNode
}


export function TableNoRecentsErrorMessage( { children }: TableNoRecentsErrorMessageProps )
{
    return (
        <Card variant='medium'>
            <CardDescription variant='medium'>
                { children }
            </CardDescription>
        </Card>
    );
}