"""another migration

Revision ID: 7a394a5454b6
Revises: 64fe9d142970
Create Date: 2024-09-14 00:41:37.279654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a394a5454b6'
down_revision: Union[str, None] = '64fe9d142970'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
