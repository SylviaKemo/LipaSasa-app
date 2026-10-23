"""add default to users created_at

Revision ID: 81dc3341abfe
Revises: d1cc01b2d2c5
Create Date: 2026-10-23 08:28:48.495099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81dc3341abfe'
down_revision: Union[str, Sequence[str], None] = 'd1cc01b2d2c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "created_at", server_default=sa.func.now())


def downgrade() -> None:
    op.alter_column("users", "created_at", server_default=None)