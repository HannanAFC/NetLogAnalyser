import { requestWsTicket } from '#/features/live-feed/api';
import { server } from '#/../test/mocks/server';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

describe( 'requestWsTicket', ( ) =>
{
	it( 'returns the ticket string on success', async( ) =>
	{
		const ticket = await requestWsTicket( );

		expect( ticket ).toBe( 'fake-ws-ticket' );
	} );

	it( 'throws when the backend returns a non-2xx status', async( ) =>
	{
		server.use(
			http.post( '*/ws/ticket', ( ) =>
			{
				return HttpResponse.json( { detail: 'Unauthorized' }, { status: 401 } );
			} )
		);

		await expect( requestWsTicket( ) ).rejects.toBeTruthy( );
	} );

	it( 'returns undefined when the response is missing the ticket field', async( ) =>
	{
		server.use(
			http.post( '*/ws/ticket', ( ) =>
			{
				return HttpResponse.json( { expires_in: 30 } );
			} )
		);

		// Typed as WsTicketResponse but no runtime validation — returns undefined
		const ticket = await requestWsTicket( );

		expect( ticket ).toBeUndefined( );
	} );
} );
