"""another migration

Revision ID: aef25f50b0f0
Revises: f7199dd2d366
Create Date: 2024-09-14 00:15:53.395135

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aef25f50b0f0'
down_revision: Union[str, None] = 'f7199dd2d366'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
