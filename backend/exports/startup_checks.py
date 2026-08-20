from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from config import settings

logger = logging.getLogger( __name__ )


def verify_export_storage( ) -> None:
	"""
	Helper to verify that the worker and fastapi app are synced up to the same volume.
	"""
	if settings.export_storage_backend != "local":
		return  # Not applicable to S3

	path = Path.cwd( ) / Path( settings.export_local_path )

	if not path.is_absolute( ):
		raise RuntimeError(
			f"EXPORT_LOCAL_PATH must be an absolute path, got {settings.export_local_path!r}. "
		)

	path.mkdir( parents=True, exist_ok=True )

	# check write permissions
	probe = path / f".startup-probe-{ uuid.uuid4( ).hex }"
	try:
		probe.write_text( "ok" )
		probe.unlink( )
	except OSError as exc:
		raise RuntimeError( f"EXPORT_LOCAL_PATH ({ path }) exists but isn't writable: { exc }") from exc

	if os.environ.get( "RUNNING_IN_CONTAINER" ) == "true" and not os.path.ismount( path ):
		raise RuntimeError(
			f"EXPORT_LOCAL_PATH ({ path }) is not a Docker volume mount point, but "
			f"RUNNING_IN_CONTAINER=true. This container's exports will NOT be "
			f"visible to any other container. Check that docker-compose.yml's "
			f"volumes: entry for this service has a container-side path that "
			f"exactly matches EXPORT_LOCAL_PATH."
		)

	logger.info( f"Export storage verified: backend=local path={ path } is_mount={ os.path.ismount( path ) }" )