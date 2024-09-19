"""another migration

Revision ID: 34c8b966911d
Revises: def663cb649f
Create Date: 2024-09-15 09:18:43.438545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34c8b966911d'
down_revision: Union[str, None] = 'def663cb649f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
