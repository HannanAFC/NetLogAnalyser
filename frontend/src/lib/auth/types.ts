import type { User } from '../users/types';

export interface AuthTokenResponse
{
	access_token: string;
	token_type: string;
	user: User;
}

export interface RegisterResponse
{
	user: User;
}

export interface RefreshResponse
{
	access_token: string;
	token_type: string;
	user: User;
}