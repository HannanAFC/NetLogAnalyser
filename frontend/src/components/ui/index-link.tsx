import { Link } from '@tanstack/react-router';

export function IndexLink( )
{
    return (
        <Link to="/" className="flex items-center gap-2.5 no-underline">
            <div className="h-2 w-2 rounded-sm bg-accent" />
            <span className="text-sm font-semibold tracking-[-0.02em] text-text-primary">
                NetLogAnalyser
            </span>
        </Link>
    );
}