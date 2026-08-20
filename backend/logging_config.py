from __future__ import annotations

import logging
import sys


def configure_logging( level: int = logging.INFO ) -> None:
	root = logging.getLogger( )
	if root.handlers:
		# Already configured - avoid attaching a second handler, which
		# would print every line twice.
		return

	handler = logging.StreamHandler( sys.stdout )
	handler.setFormatter( logging.Formatter(
		"%(asctime)s %(levelname)s %(name)s: %(message)s"
	) )
	root.addHandler( handler )
	root.setLevel( level )

	logging.getLogger( "arq.worker" ).setLevel( level )