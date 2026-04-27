"""add_sender_column

Revision ID: 45e5bb6a0a64
Revises: 2814228321dc
Create Date: 2026-04-27 15:34:14.993314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45e5bb6a0a64'
down_revision: Union[str, Sequence[str], None] = '2814228321dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajout de la colonne sender
    op.add_column('demandes', sa.Column('sender', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Suppression de la colonne
    op.drop_column('demandes', 'sender')
