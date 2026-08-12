import { cn } from '#/lib/utils';
import { Card } from '../ui/card';
import type { CardProps } from '../ui/card';

interface MapPopupProps extends CardProps
{
    left: number;
    top:  number;
};

export function MapPopup( { className, variant = 'default', glow, children, left, top, ...props }: MapPopupProps )
{
    return (
        <Card
            className={ cn( className, 'fixed pointer-events-none transition-[top,left] z-10' ) }
            style={
                {
                    top:  top,
                    left: left
                }
            }
            variant={ variant }
            glow={ glow }
            { ...props }
        >
            { children }
        </Card>
    );
}