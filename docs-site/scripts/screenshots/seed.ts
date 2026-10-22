// Creates a demo account, API keys and a deterministic spread of traffic so every screenshot is populated.

export interface DemoData
{
    email:    string;
    password: string;
}

export const demo: DemoData = { email: 'demo@example.com', password: 'Demo-Passw0rd-2026' };

const displayName = 'Alex';
const keyLabels   = [ 'Edge router', 'Office firewall', 'Home lab', 'CI sensor' ];

// Public addresses in a spread of countries (checked against GeoLite2).
// Anycast addresses such as 1.1.1.1 and 9.9.9.9 have no country and would show up as blank cells.
// Weight controls how much traffic each one sends.
const remoteHosts: { ip: string; weight: number }[] =
[
    { ip: '8.8.8.8',         weight: 13 }, // US
    { ip: '64.233.160.1',    weight: 5  }, // US
    { ip: '85.214.132.117',  weight: 11 }, // DE
    { ip: '212.58.244.20',   weight: 9  }, // GB
    { ip: '80.67.169.12',    weight: 7  }, // FR
    { ip: '114.114.114.114', weight: 9  }, // CN
    { ip: '77.88.8.8',       weight: 8  }, // RU
    { ip: '200.160.2.3',     weight: 7  }, // BR
    { ip: '1.128.0.1',       weight: 7  }, // AU
    { ip: '202.12.27.33',    weight: 6  }, // JP
    { ip: '168.126.63.1',    weight: 4  }, // KR
    { ip: '196.216.2.1',     weight: 4  }, // ZA
    { ip: '24.114.0.1',      weight: 5  }, // CA
    { ip: '49.32.0.1',       weight: 5  }  // IN
];

const internalHosts  = [ '10.0.1.12', '10.0.1.25', '10.0.2.7', '10.0.2.40', '10.0.3.5', '192.168.1.20', '192.168.1.44' ];
const webPorts       = [ 443, 443, 443, 80, 8080, 8443 ];
const bursts         = [ 7, 19, 33, 46, 52 ];

type Entry = Record<string, unknown>;

// mulberry32, so reruns generate the same traffic shape
function prng( seed: number )
{
    let a = seed;
    return ( ) =>
    {
        a = ( a + 0x6D2B79F5 ) | 0;
        let t = Math.imul( a ^ ( a >>> 15 ), 1 | a );
        t = ( t + Math.imul( t ^ ( t >>> 7 ), 61 | t ) ) ^ t;
        return ( ( t ^ ( t >>> 14 ) ) >>> 0 ) / 4294967296;
    };
}

async function api<T>( backend: string, path: string, init: RequestInit = { } ): Promise<{ status: number; body: T }>
{
    const response = await fetch( `${ backend }${ path }`, init );
    const text     = await response.text( );
    return { status: response.status, body: ( text ? JSON.parse( text ) : null ) as T };
}

const post = ( body: unknown, headers: Record<string, string> = { } ): RequestInit =>
    ( { method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify( body ) } );

// With EMAIL_VERIFICATION_ENABLED the demo account must be verified before it can log in. The backend's test-only
// endpoints (ENABLE_TEST_ENDPOINTS) expose the verification token, which needs TEST_ENDPOINT_KEY to be exported here too.
async function verifyEmail( backend: string ): Promise<boolean>
{
    const key = process.env.TEST_ENDPOINT_KEY;
    if ( !key ) return false;

    const captured = await api<{ token: string }>( backend, `/test-only/last-token?email=${ encodeURIComponent( demo.email ) }&token_type=verification`, { headers: { 'x-test-endpoint-key': key } } );
    if ( captured.status !== 200 ) return false;

    const verified = await api( backend, `/auth/verify-email?token=${ encodeURIComponent( captured.body.token ) }` );
    return verified.status === 200;
}

async function login( backend: string ): Promise<string>
{
    const attempt = ( ) => api<{ access_token: string }>( backend, '/auth/login', post( { email: demo.email, password: demo.password } ) );

    let result = await attempt( );
    if ( result.status === 401 )
    {
        const registered = await api( backend, '/auth/register',
            post( { email: demo.email, display_name: displayName, password: demo.password, confirm_password: demo.password } ) );
        if ( registered.status !== 201 )
        {
            throw new Error( `Could not register the demo account (${ registered.status }): ${ JSON.stringify( registered.body ) }` );
        }
        result = await attempt( );
    }
    if ( result.status === 403 && await verifyEmail( backend ) )
    {
        result = await attempt( );
    }
    if ( result.status === 429 )
    {
        throw new Error( 'The backend rate limited the demo login (RATELIMIT_AUTH_TIMES per window). Wait a minute and try again.' );
    }
    if ( result.status !== 200 )
    {
        throw new Error(
            `Could not log in as the demo account (${ result.status }). Email verification looks enabled: either set EMAIL_VERIFICATION_ENABLED=false, `
            + 'or set ENABLE_TEST_ENDPOINTS=true and TEST_ENDPOINT_KEY on the backend and export the same TEST_ENDPOINT_KEY here (the demo email must end in TEST_EMAIL_DOMAIN).' );
    }
    return result.body.access_token;
}

// Replace the demo user's keys with a fresh set, so the settings page is tidy and we hold the plaintext of every key.
async function resetKeys( backend: string, token: string ): Promise<string[]>
{
    const auth = { authorization: `Bearer ${ token }` };
    const existing = await api<{ id: string; revoked_at: string | null }[]>( backend, '/api-keys', { headers: auth } );
    for ( const key of existing.body.filter( ( k ) => !k.revoked_at ) )
    {
        await api( backend, `/api-keys/${ key.id }`, { method: 'DELETE', headers: auth } );
    }

    const keys: string[] = [ ];
    for ( const label of keyLabels )
    {
        const created = await api<{ api_key: string }>( backend, '/api-keys', post( { label }, auth ) );
        if ( created.status !== 201 )
        {
            throw new Error( `Could not create API key "${ label }" (${ created.status })` );
        }
        keys.push( created.body.api_key );
    }
    return keys;
}

function buildTraffic( now: number, minutes: number, random: ( ) => number ): Entry[ ][ ]
{
    const pick = <T>( items: T[ ] ): T => items[ Math.floor( random( ) * items.length ) ];
    const totalWeight = remoteHosts.reduce( ( sum, h ) => sum + h.weight, 0 );
    const remote = ( ) =>
    {
        let roll = random( ) * totalWeight;
        for ( const host of remoteHosts )
        {
            roll -= host.weight;
            if ( roll <= 0 ) return host.ip;
        }
        return remoteHosts[ 0 ].ip;
    };

    const buckets: Entry[ ][ ] = [ ];

    for ( let minute = 0; minute < minutes; minute++ )
    {
        const bucket: Entry[ ] = [ ];
        const age     = minutes - minute; // minutes before now
        const wave    = 1 + 0.35 * Math.sin( minute / 5 ) + ( random( ) - 0.5 ) * 0.25;
        const recent  = age <= 15 ? 1.4 : 1;
        const burst   = bursts.includes( minute ) ? 2.2 : 1;
        const volume  = Math.round( 90 * wave * recent * burst );

        for ( let i = 0; i < volume; i++ )
        {
            const roll = random( );
            const captured_at = new Date( now - age * 60_000 + random( ) * 60_000 ).toISOString( );
            let entry: Entry;

            if ( roll < 0.1 )
            {
                entry = { src_ip: pick( internalHosts ), dst_ip: remote( ), src_port: 40000 + Math.floor( random( ) * 20000 ), dst_port: 53, protocol: 'UDP', packet_size_bytes: 70 + Math.floor( random( ) * 80 ), raw_payload: { }, captured_at };
            }
            else if ( roll < 0.18 )
            {
                entry = { src_ip: pick( internalHosts ), dst_ip: remote( ), src_port: 0, dst_port: 0, protocol: 'ICMP', packet_size_bytes: 64 + Math.floor( random( ) * 40 ), raw_payload: { }, captured_at };
            }
            else if ( roll < 0.65 )
            {
                entry = { src_ip: remote( ), dst_ip: pick( internalHosts ), src_port: 30000 + Math.floor( random( ) * 30000 ), dst_port: pick( webPorts ), protocol: 'TCP', packet_size_bytes: 200 + Math.floor( random( ) * 1250 ), flags: pick( [ 'ACK', 'PSH,ACK', 'SYN', 'SYN,ACK', 'FIN,ACK' ] ), raw_payload: { }, captured_at };
            }
            else
            {
                entry = { src_ip: pick( internalHosts ), dst_ip: remote( ), src_port: 30000 + Math.floor( random( ) * 30000 ), dst_port: pick( webPorts ), protocol: 'TCP', packet_size_bytes: 120 + Math.floor( random( ) * 1380 ), flags: pick( [ 'ACK', 'PSH,ACK', 'ACK' ] ), raw_payload: { }, captured_at };
            }

            bucket.push( entry );
        }

        // A sprinkling of single-packet anomalies
        for ( let i = 0; i < 3 + Math.floor( random( ) * 4 ); i++ )
        {
            const captured_at = new Date( now - age * 60_000 + random( ) * 60_000 ).toISOString( );
            const kind = Math.floor( random( ) * 4 );
            const src_ip = pick( [ '114.114.114.114', '77.88.8.8', '185.228.168.9', '103.86.96.100' ] );
            const base = { src_ip, dst_ip: pick( internalHosts ), src_port: 40000 + Math.floor( random( ) * 20000 ), raw_payload: { }, captured_at };

            if ( kind === 0 )      bucket.push( { ...base, dst_port: 22,   protocol: 'TCP', packet_size_bytes: 60,   flags: 'FIN,PSH,URG' } );
            else if ( kind === 1 ) bucket.push( { ...base, dst_port: 3389, protocol: 'TCP', packet_size_bytes: 40,   flags: 'SYN,FIN' } );
            else if ( kind === 2 ) bucket.push( { ...base, dst_port: 443,  protocol: 'UDP', packet_size_bytes: 9100 } );
            else                   bucket.push( { ...base, dst_port: 23,   protocol: 'TCP', packet_size_bytes: 0,    flags: '' } );
        }

        buckets.push( bucket );
    }

    // Scans must arrive in a single batch to be seen by the batch-level heuristics
    const scanner = '185.228.168.9';
    const target  = '10.0.1.12';
    const scanAt  = ( ) => new Date( now - ( 10 + random( ) * 40 ) * 60_000 ).toISOString( );
    buckets.push( Array.from( { length: 40 }, ( _, i ) => ( { src_ip: scanner, dst_ip: target, src_port: 51000, dst_port: 20 + i * 37, protocol: 'TCP', packet_size_bytes: 44, flags: 'SYN', raw_payload: { }, captured_at: scanAt( ) } ) ) );
    buckets.push( Array.from( { length: 30 }, ( _, i ) => ( { src_ip: '103.86.96.100', dst_ip: `10.0.${ 1 + ( i % 3 ) }.${ 100 + i }`, src_port: 52000, dst_port: 445, protocol: 'TCP', packet_size_bytes: 44, flags: 'SYN', raw_payload: { }, captured_at: scanAt( ) } ) ) );

    return buckets;
}

export async function ingest( backend: string, keys: string[ ], batches: Entry[ ][ ] ): Promise<number>
{
    let accepted = 0;
    let n = 0;
    for ( const batch of batches )
    {
        for ( let i = 0; i < batch.length; i += 250 )
        {
            const response = await api<{ accepted: number; rejected: number }>( backend, '/ingest',
                post( { entries: batch.slice( i, i + 250 ) }, { 'x-api-key': keys[ n++ % keys.length ] } ) );
            if ( response.status >= 300 )
            {
                throw new Error( `Ingest failed (${ response.status }): ${ JSON.stringify( response.body ) }` );
            }
            accepted += response.body.accepted;
        }
    }
    return accepted;
}

// A short burst timestamped "now", sent right before capturing so the live feed shows entries a few seconds old
export function freshTraffic( count: number ): Entry[ ][ ]
{
    const now = Date.now( );
    const entries = buildTraffic( now, 1, prng( 7 ) )[ 0 ].slice( 0, count );
    return [ entries.map( ( entry, i ) => ( { ...entry, captured_at: new Date( now - i * 700 ).toISOString( ) } ) ) ];
}

export async function seed( backend: string ): Promise<string[ ]>
{
    const token = await login( backend );
    const keys  = await resetKeys( backend, token );
    const accepted = await ingest( backend, keys, buildTraffic( Date.now( ), 60, prng( 20261022 ) ) );
    console.log( `Seeded ${ accepted } entries across ${ keys.length } API keys` );
    return keys;
}
