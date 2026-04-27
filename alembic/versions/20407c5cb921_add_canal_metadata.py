"""add_canal_metadata

Revision ID: 20407c5cb921
Revises: 
Create Date: 2026-04-27 14:20:42.992802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20407c5cb921'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajout des colonnes
    op.add_column('demandes', sa.Column('received_at', sa.DateTime(), nullable=True))
    op.add_column('demandes', sa.Column('external_id', sa.String(length=255), nullable=True))
    op.add_column('demandes', sa.Column('canal_metadata', sa.JSON(), nullable=True))
    
    # Ajout de l'index unique sur (canal, external_id)
    op.create_index('idx_canal_external_id', 'demandes', ['canal', 'external_id'], unique=True)


def downgrade() -> None:
    # Suppression de l'index
    op.drop_index('idx_canal_external_id', table_name='demandes')
    
    # Suppression des colonnes
    op.drop_column('demandes', 'canal_metadata')
    op.drop_column('demandes', 'external_id')
    op.drop_column('demandes', 'received_at')
