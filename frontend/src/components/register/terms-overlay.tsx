import type { HTMLAttributes } from 'react';
import { TermsContent } from '../legal/terms-content';
import { Card } from '../ui/card';
import { Heading } from '../ui/heading';
import { cn } from '#/lib/utils';
import { Button } from '../ui/button';
import { X } from 'lucide-react';

type ComponentCallback = ( ...args: any[ ] ) => void;

interface TermsOverlayProps extends HTMLAttributes< HTMLDivElement >
{
    onConfirm: ComponentCallback;
}

export function TermsOverlay( { className, onConfirm, ...props }: TermsOverlayProps )
{
    return (
        <Card
            className={ cn( 'max-w-[calc(100vw-32px)] max-h-[calc(100vh-32px)] overflow-auto', className ) }
            { ...props }
        >
            <div className='flex flex-row items-center gap-4 justify-between mb-6'>
                <Heading level='h2'>Terms & Conditions</Heading>
                <Button
                    variant='ghost'
                    onClick={ onConfirm }
                >
                    <X className="h-6 w-6" />
                </Button>
            </div>
            <TermsContent />
        </Card>
    );
}