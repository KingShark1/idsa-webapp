"""another migration

Revision ID: 5e2482aca03a
Revises: 109a574b56ff
Create Date: 2024-09-15 09:28:14.661949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e2482aca03a'
down_revision: Union[str, None] = '109a574b56ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
