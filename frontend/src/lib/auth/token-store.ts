/** 
 * This is where the JWT token is stored, token is stored in memory
 * Does not handle auth state.
*/
let accessToken: string | null = null;

export const tokenStore =
{
    get: ( ) => accessToken,
    set: ( token: string | null ) =>
    {
        accessToken = token;
    }
}