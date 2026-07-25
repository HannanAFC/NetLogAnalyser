import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { BodySm } from './heading';

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
				'rounded-lg border bg-card p-5 shadow-card',
				'border-border',
				glow && [
					'relative overflow-hidden transition-[border-color,background] duration-150',
					'hover:border-success/25',
					/* Pseudo-element glow overlay */
					'before:absolute before:inset-0 before:bg-success/3 before:opacity-0 before:transition-opacity before:duration-200',
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
				'font-mono text-[11px] font-medium text-success tracking-[0.08em] uppercase',
				className
			) }
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
		<BodySm
			className={ cn( 'text-text-secondary leading-relaxed', className ) }
			{ ...props }
		>
			{ children }
		</BodySm>
	);
}
