"""Merge contact_management and milestone_7 models

Revision ID: 3be69ae0f76c
Revises: 20261111_add_contact_management_models, 20261111_milestone_7_models
Create Date: 2026-11-12 09:07:27.072596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3be69ae0f76c'
down_revision: Union[str, Sequence[str], None] = ('20261111_add_contact_management_models', '20261111_milestone_7_models')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
