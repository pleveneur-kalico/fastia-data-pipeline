"""add_dedup_status

Revision ID: 2814228321dc
Revises: 20407c5cb921
Create Date: 2026-04-27 15:31:50.337751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2814228321dc'
down_revision: Union[str, Sequence[str], None] = '20407c5cb921'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajout de la colonne dedup_status
    op.add_column('demandes', sa.Column('dedup_status', sa.String(length=30), nullable=False, server_default='original'))

    # Ajout d'un index sur received_at pour la performance des requêtes de déduplication temporelle
    op.create_index('idx_demandes_received_at', 'demandes', ['received_at'])


def downgrade() -> None:
    # Suppression de l'index
    op.drop_index('idx_demandes_received_at', table_name='demandes')

    # Suppression de la colonne
    op.drop_column('demandes', 'dedup_status')
