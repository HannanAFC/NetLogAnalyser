import type { InputHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from '../../lib/utils';

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
                        'mt-1 w-full rounded-md border px-3 py-2 font-sans text-sm',
                        'bg-surface-card border-border text-text-primary',
                        'placeholder:text-text-tertiary',
                        'focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500/40',
                        'transition-[border-color,box-shadow] duration-150',
                        error && 'border-critical focus:border-critical focus:ring-critical/40',
                        className
                    )}
                    { ...props }
                />
                { error && (
                    <p className='mt-1 text-xs text-critical'>{ error }</p>
                )}
            </div>
        );
    }
);

Input.displayName = 'Input';
