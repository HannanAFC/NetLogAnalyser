import { type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '#/lib/utils';

type BadgeVariant =
    | 'default'
    | 'jwt'
    | 'key'
    | 'critical'
    | 'high'
    | 'medium'
    | 'low'
    | 'info'
    | 'success';

const variantClasses: Record< BadgeVariant, string > =
{
    default: 'bg-text-tertiary/10 text-text-secondary border-border-hi',
    jwt: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
    key: 'bg-amber-500/12 text-amber-500 border-amber-500/20',
    critical: 'bg-critical/12 text-critical border-critical/20',
    high: 'bg-high/12 text-high border-high/20',
    medium: 'bg-medium/12 text-medium border-medium/20',
    low: 'bg-low/12 text-low border-low/20',
    info: 'bg-info/12 text-info border-info/20',
    success: 'bg-green-500/12 text-green-500 border-green-500/20'
};

export interface BadgeProps extends HTMLAttributes< HTMLSpanElement >
{
    variant?: BadgeVariant;
    children: ReactNode;
}

export function Badge(
{
    variant = 'default',
    className,
    children,
    ...props
}: BadgeProps )
{
    return (
        <span
            className={ cn(
                'inline-flex items-center font-mono text-[10px] font-medium',
                'px-1.75 py-0.5 rounded-sm border',
                'tracking-[0.04em]',
                variantClasses[ variant ],
                className
            ) }
            { ...props }
        >
            { children }
        </span>
    );
}
