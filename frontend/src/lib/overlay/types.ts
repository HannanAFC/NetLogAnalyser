import type { ReactNode } from 'react';

export interface OverlayOptions
{
	id?:          string;
	onClose?:     ( ) => void;
	dismissible?: boolean
}

export interface OverlayItem
{
	id:          string;
	content:     ReactNode;
	dismissible: boolean;
	onClose?:    ( ) => void
}