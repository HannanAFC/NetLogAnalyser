export interface User
{
  id:           string;
  email:        string;
  display_name: string;
  created_at:   string;
}

export interface AuthTokenResponse
{
  access_token: string;
  token_type:   string;
  user:         User;
}

export interface RegisterResponse
{
  user: User;
}

export interface RefreshResponse
{
    access_token: string;
    token_type:   string;
    user:         User;
}
