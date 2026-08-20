import { cn } from '#/lib/utils';
import type { HTMLAttributes } from 'react';
import { PrivacyPolicyContent } from '../legal/privacy-policy-content';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Heading } from '../ui/heading';
import { X } from 'lucide-react';

type ComponentCallback = ( ...args: any[ ] ) => void;

interface PrivacyOverlayProps extends HTMLAttributes< HTMLDivElement >
{
    onConfirm: ComponentCallback;
}

export function PrivacyOverlay( { className, onConfirm, ...props }: PrivacyOverlayProps )
{
    return (
        <Card
            className={ cn( 'max-w-[calc(100vw-32px)] max-h-[calc(100vh-32px)] overflow-auto', className ) }
            { ...props }
        >
            <div className='flex flex-row items-center gap-4 justify-between mb-6'>
                <Heading level='h2'>Privacy Policy</Heading>
                <Button
                    variant='ghost'
                    onClick={ onConfirm }
                >
                    <X className="h-6 w-6" />
                </Button>
            </div>
            <PrivacyPolicyContent />
        </Card>
    );
}