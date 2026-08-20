from __future__ import annotations

import json
from typing import Any

from models.models import LogEntry

EXPORT_FIELDNAMES = [
	"id",
	"captured_at",
	"src_ip",
	"dst_ip",
	"src_port",
	"dst_port",
	"protocol",
	"packet_size_bytes",
	"flags",
	"src_country_code",
	"src_geo_status",
	"dst_country_code",
	"dst_geo_status",
	"anomaly_score",
	"anomaly_reasons",
	"raw_payload"
]


def to_export_dict( entry: LogEntry ) -> dict[ str, Any]:
	"""
	Returns dict version of log entry.
	Parameters:
		entry (LogEntry): Entry to convert.
	Returns:
		converted (dict[ str, Any ]): Converted log entry.
	"""
	return {
		"id":                entry.id,
		"captured_at":       entry.captured_at,
		"src_ip":            str( entry.src_ip ),
		"dst_ip":            str( entry.dst_ip ),
		"src_port":          entry.src_port,
		"dst_port":          entry.dst_port,
		"protocol":          entry.protocol,
		"packet_size_bytes": entry.packet_size_bytes,
		"flags":             entry.flags,
		"src_country_code":  entry.src_country_code,
		"src_geo_status":    entry.src_geo_status,
		"dst_country_code":  entry.dst_country_code,
		"dst_geo_status":    entry.dst_geo_status,
		"anomaly_score":     entry.anomaly_score,
		"anomaly_reasons":   entry.anomaly_reasons,
		"raw_payload":       entry.raw_payload
	}

def flatten_for_csv( row: dict[ str, Any ] ) -> dict[ str, Any ]:
	"""
	Flattens a log entry dictionary in order to remove nesting for CSV conversion.
	Parameters:
		row (dict[str, Any]): Log entry dict.
	Returns:
		flattened (dict[str, Any]): Flattened log entry dict.
	"""
	flat = dict( row )
	flat[ "anomaly_reasons" ] = json.dumps( row[ "anomaly_reasons" ], default=str )
	flat[ "raw_payload" ]     = json.dumps( row[ "raw_payload" ], default=str )
	flat[ "captured_at" ]     = row[ "captured_at" ].isoformat( )
	return flat