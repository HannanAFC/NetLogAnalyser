import { apiClient } from '#/lib/api/client';

interface WsTicketResponse
{
	ticket:     string
	expires_in: number
}

export async function requestWsTicket( ): Promise< string >
{
	const { data } = await apiClient.post< WsTicketResponse >( '/ws/ticket' );
	return data.ticket;
}