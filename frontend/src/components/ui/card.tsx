import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface CardProps extends HTMLAttributes< HTMLDivElement >
{
	children: ReactNode;
	glow?: boolean;
}

export function Card( { className, glow, children, ...props }: CardProps )
{
	return (
		<div
			className={ cn(
				'rounded-lg border bg-surface-card p-5',
				'border-border',
				glow && [
					'relative overflow-hidden transition-[border-color,background] duration-150',
					'hover:border-green-500/25',
					/* Pseudo-element glow overlay */
					'before:absolute before:inset-0 before:bg-green-500/3 before:opacity-0 before:transition-opacity before:duration-200',
					'hover:before:opacity-100'
				],
				className
			) }
			{ ...props }
		>
			{ children }
		</div>
	);
}

/* ── Card sub-components ───────────────────────────────────────────── */

export function CardLabel( { className, children, ...props }: HTMLAttributes< HTMLSpanElement > )
{
	return (
		<span
			className={ cn(
				'font-mono text-[11px] font-medium text-green-500 tracking-[0.08em] uppercase',
				className
			)}
			{ ...props }
		>
			{ children }
		</span>
	);
}

export function CardTitle( { className, children, ...props }: HTMLAttributes< HTMLHeadingElement > )
{
	return (
		<h3
			className={ cn( 'text-sm font-medium text-text-primary', className ) }
			{ ...props }
		>
			{ children }
		</h3>
	);
}

export function CardDescription( { className, children, ...props }: HTMLAttributes< HTMLParagraphElement > )
{
	return (
		<p
			className={ cn( 'text-xs text-text-secondary leading-relaxed', className ) }
			{ ...props }
		>
			{ children }
		</p>
	);
}
