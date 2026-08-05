import { logEntryBatchMessageSchema } from '#/features/live-feed/schemas';
import { describe, expect, it } from 'vitest';

const VALID_BATCH = {
	type: 'log_entry_batch',
	data: [
		{
			src_ip:            '10.0.0.1',
			dst_ip:            '10.0.0.2',
			src_port:          443,
			dst_port:          8080,
			protocol:          'TCP',
			packet_size_bytes: 1500,
			flags:             'SYN',
			country_code:      'US',
			anomaly_score:     0.05,
			anomaly_reasons:   [ ],
			captured_at:       '2025-08-01T12:00:00Z'
		}
	]
};

describe( 'logEntryBatchMessageSchema', ( ) =>
{
	it( 'accepts a valid log_entry_batch message', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse( VALID_BATCH );

		expect( result.success ).toBe( true );
	} );

	it( 'accepts a batch with multiple entries', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'log_entry_batch',
			data: [ VALID_BATCH.data[ 0 ], VALID_BATCH.data[ 0 ] ]
		} );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.data ).toHaveLength( 2 );
		}
	} );

	it( 'accepts an entry with id and nullable fields as null', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'log_entry_batch',
			data: [
				{
					id:                42,
					src_ip:            '10.0.0.1',
					dst_ip:            '10.0.0.2',
					src_port:          443,
					dst_port:          8080,
					protocol:          'TCP',
					packet_size_bytes: 1500,
					flags:             null,
					country_code:      null,
					anomaly_score:     0,
					anomaly_reasons:   [ ],
					captured_at:       '2025-08-01T12:00:00Z'
				}
			]
		} );

		expect( result.success ).toBe( true );
	} );

	it( 'rejects when type is missing', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			data: VALID_BATCH.data
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects when type is not "log_entry_batch"', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'other_message',
			data: VALID_BATCH.data
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects when data is missing', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'log_entry_batch'
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects when data is not an array', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'log_entry_batch',
			data: 'not-an-array'
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects an entry with an invalid protocol', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'log_entry_batch',
			data: [
				{
					...VALID_BATCH.data[ 0 ],
					protocol: 'HTTP'
				}
			]
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects an entry missing a required field', ( ) =>
	{
		const { src_ip, ...missingSrcIp } = VALID_BATCH.data[ 0 ];

		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'log_entry_batch',
			data: [ missingSrcIp ]
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'rejects an entry with a string port instead of number', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type: 'log_entry_batch',
			data: [
				{
					...VALID_BATCH.data[ 0 ],
					src_port: '443'
				}
			]
		} );

		expect( result.success ).toBe( false );
	} );

	it( 'strips unknown top-level fields', ( ) =>
	{
		const result = logEntryBatchMessageSchema.safeParse(
		{
			type:     'log_entry_batch',
			data:     VALID_BATCH.data,
			extraKey: 'should-be-stripped'
		} );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data ).not.toHaveProperty( 'extraKey' );
		}
	} );
} );
