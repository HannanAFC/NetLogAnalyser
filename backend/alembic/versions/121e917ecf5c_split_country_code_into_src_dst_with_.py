"""split country_code into src/dst with geo_status

Revision ID: 121e917ecf5c
Revises: 76d5d7263919
Create Date: 2026-08-07 18:10:25.138578

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '121e917ecf5c'
down_revision: Union[str, Sequence[str], None] = '76d5d7263919'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    geo_status_enum = postgresql.ENUM(
        "RESOLVED", "PRIVATE", "UNRESOLVED", "UNAVAILABLE",
        name="geo_status"
    )
    geo_status_enum.create( op.get_bind( ) )

    op.add_column('log_entries', sa.Column('src_country_code', sa.String(length=2), nullable=True))
    op.add_column('log_entries', sa.Column('dst_country_code', sa.String(length=2), nullable=True))
    op.add_column('log_entries', sa.Column('src_geo_status' ,geo_status_enum, nullable=False))
    op.add_column('log_entries', sa.Column('dst_geo_status', geo_status_enum, nullable=False))
    op.drop_index(op.f('ix_log_entries_country_code'), table_name='log_entries')
    op.create_index(op.f('ix_log_entries_dst_geo_status'), 'log_entries', ['dst_geo_status'], unique=False)
    op.create_index(op.f('ix_log_entries_src_geo_status'), 'log_entries', ['src_geo_status'], unique=False)
    op.drop_column('log_entries', 'country_code')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('log_entries', sa.Column('country_code', sa.VARCHAR(length=2), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_log_entries_src_geo_status'), table_name='log_entries')
    op.drop_index(op.f('ix_log_entries_dst_geo_status'), table_name='log_entries')
    op.create_index(op.f('ix_log_entries_country_code'), 'log_entries', ['country_code'], unique=False)
    op.drop_column('log_entries', 'dst_geo_status')
    op.drop_column('log_entries', 'src_geo_status')
    op.drop_column('log_entries', 'dst_country_code')
    op.drop_column('log_entries', 'src_country_code')
    postgresql.ENUM( name="geo_status" ).drop( op.get_bind( ) )