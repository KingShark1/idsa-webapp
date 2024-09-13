"""another migration

Revision ID: def663cb649f
Revises: 7a394a5454b6
Create Date: 2024-09-14 00:45:28.407215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'def663cb649f'
down_revision: Union[str, None] = '7a394a5454b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
