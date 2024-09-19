"""another migration

Revision ID: 109a574b56ff
Revises: 34c8b966911d
Create Date: 2024-09-15 09:27:16.798958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '109a574b56ff'
down_revision: Union[str, None] = '34c8b966911d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
