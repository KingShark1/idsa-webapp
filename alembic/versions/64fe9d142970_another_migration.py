"""another migration

Revision ID: 64fe9d142970
Revises: aef25f50b0f0
Create Date: 2024-09-14 00:17:51.894398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64fe9d142970'
down_revision: Union[str, None] = 'aef25f50b0f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
