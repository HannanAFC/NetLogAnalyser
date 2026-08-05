import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { BodySm } from './heading';

/* ── Card variants ─────────────────────────────────────────────────── */

export type CardVariant =
	| 'default'
	| 'jwt'
	| 'key'
	| 'critical'
	| 'high'
	| 'medium'
	| 'low'
	| 'info'
	| 'success';

const cardVariantClasses: Record< CardVariant, string > =
	{
		default:  'border-border bg-card',
		jwt:      'border-blue-500/25 bg-blue-500/6',
		key:      'border-amber-500/25 bg-amber-500/5',
		critical: 'border-critical/25 bg-critical/6',
		high:     'border-high/25 bg-high/6',
		medium:   'border-medium/25 bg-medium/6',
		low:      'border-low/25 bg-low/6',
		info:     'border-info/25 bg-info/6',
		success:  'border-success/25 bg-success/6'
	};

const labelVariantClasses: Record< CardVariant, string > =
	{
		default:  'text-text-tertiary',
		jwt:      'text-blue-500',
		key:      'text-amber-500',
		critical: 'text-critical',
		high:     'text-high',
		medium:   'text-medium',
		low:      'text-low',
		info:     'text-info',
		success:  'text-success'
	};

/* ── Card ──────────────────────────────────────────────────────────── */

export interface CardProps extends HTMLAttributes< HTMLDivElement >
{
	children: ReactNode;
	variant?: CardVariant;
	glow?:    boolean;
}

export function Card( { className, variant = 'default', glow, children, ...props }: CardProps )
{
	return (
		<div
			className={ cn(
				'rounded-lg border p-5 shadow-card transition-[border-color,background] duration-150',
				cardVariantClasses[ variant ],
				glow && [
					'relative overflow-hidden',
					'hover:border-success/30',
					/* Pseudo-element glow overlay */
					'before:absolute before:inset-0 before:bg-success/3 before:opacity-0 before:transition-opacity before:duration-200',
					'hover:before:opacity-100'
				],
				className
			) }
			data-card-variant={ variant }
			{ ...props }
		>
			{ children }
		</div>
	);
}

/* ── Card sub-components ───────────────────────────────────────────── */

export interface CardLabelProps extends HTMLAttributes< HTMLSpanElement >
{
	variant?: CardVariant;
}

export function CardLabel( { className, variant, children, ...props }: CardLabelProps )
{
	return (
		<span
			className={ cn(
				'font-mono text-[11px] font-medium tracking-[0.08em] uppercase',
				labelVariantClasses[ variant ?? 'success' ],
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

export interface CardDescriptionProps extends HTMLAttributes< HTMLParagraphElement >
{
	variant?: CardVariant;
}

export function CardDescription( { className, variant, children, ...props }: CardDescriptionProps )
{
	return (
		<BodySm
			className={ cn(
				'text-text-secondary leading-relaxed',
				labelVariantClasses[ variant ?? 'success' ],
				className
			) }
			{ ...props }
		>
			{ children }
		</BodySm>
	);
}
