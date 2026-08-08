import { cn } from '#/lib/utils';
import type { HTMLAttributes } from 'react';

export function SkeletonLog( { className, ...props }:  HTMLAttributes< HTMLTableRowElement > )
{
    return (
        <tr className={ cn( 'border-b border-border last:border-0 animate-pulse' ) } { ...props }>
            <td className="px-3 py-2"><div className="h-8 w-10 rounded bg-card" /></td>
            <td className="px-3 py-2"><div className="h-8 w-40 rounded bg-card" /></td>
            <td className="px-3 py-2" />
            <td className="px-3 py-2"><div className="h-8 w-40 rounded bg-card" /></td>
            <td className="px-3 py-2"><div className="h-8 w-10 rounded bg-card" /></td>
            <td className="px-3 py-2"><div className="ml-auto h-8 w-14 rounded bg-card" /></td>
            <td className="px-3 py-2"><div className="h-8 w-16 rounded bg-card" /></td>
            <td className="px-3 py-2"><div className="h-8 w-16 rounded bg-card" /></td>
            <td className="px-3 py-2"><div className="h-8 w-16 rounded bg-card" /></td>
        </tr>
    );
}