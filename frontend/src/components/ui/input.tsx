import type { InputHTMLAttributes, LabelHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { BodySm } from './heading';

/* ── Label ─────────────────────────────────────────────────────────── */

type LabelSize = 'sm' | 'xs';

const labelSizeClasses: Record<LabelSize, string> = {
	sm: 'text-sm font-medium text-text-primary',
	xs: 'text-xs font-medium text-text-secondary'
};

export interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement>
{
	size?: LabelSize;
}

export function Label( { size = 'sm', className, children, ...props }: LabelProps )
{
	return (
		<label
			className={ cn( 'block', labelSizeClasses[ size ], className ) }
			{ ...props }
		>
			{ children }
		</label>
	);
}

/* ── Input ─────────────────────────────────────────────────────────── */

export interface InputProps extends InputHTMLAttributes< HTMLInputElement >
{
	error?: string;
}

export const Input = forwardRef< HTMLInputElement, InputProps > (
	( { className, error, id, ...props }, ref ) =>
	{
		return (
			<div>
				<input
					ref={ ref }
					id={ id }
					className={ cn(
						'mt-1 w-full rounded-md border px-3 py-2.5 text-sm',
						'bg-card border-border text-text-primary',
						'placeholder:text-text-tertiary',
						'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/25',
						'transition-[border-color,box-shadow] duration-150',
						error && 'border-danger focus:border-danger focus:ring-danger/25',
						className
					) }
					{ ...props }
				/>
				{ error && (
					<BodySm className='mt-1 text-danger'>{ error }</BodySm>
				) }
			</div>
		);
	}
);

Input.displayName = 'Input';
