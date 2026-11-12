"""Add search_vector, soft delete, and PII encryption to contacts

Revision ID: 252144b6e3ee
Revises: 3be69ae0f76c
Create Date: 2026-11-12 09:09:53.350606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '252144b6e3ee'
down_revision: Union[str, Sequence[str], None] = '3be69ae0f76c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add deleted_at column for soft delete
    op.add_column('contacts', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Add search_vector column for full-text search
    op.add_column('contacts', sa.Column('search_vector', sa.TSVECTOR(), nullable=True))
    
    # Add GIN index for search_vector
    op.create_index('ix_contacts_search_vector', 'contacts', ['search_vector'], postgresql_using='gin')
    
    # Add GIN index for tags
    op.create_index('ix_contacts_tags', 'contacts', ['tags'], postgresql_using='gin')
    
    # Add columns for encrypted PII
    op.add_column('contacts', sa.Column('_email', sa.String(), nullable=False))
    op.add_column('contacts', sa.Column('_phone_number', sa.String(), nullable=True))
    
    # Data migration: encrypt existing emails and phone numbers
    op.execute("""
        UPDATE contacts SET _email = email;
    """)
    
    # Set default values for new columns
    op.execute("""
        UPDATE contacts SET _phone_number = phone_number WHERE phone_number IS NOT NULL;
    """)
    
    # Drop old columns
    op.drop_column('contacts', 'email')
    op.drop_column('contacts', 'phone_number')


def downgrade() -> None:
    """Downgrade schema."""
    # Add back old columns
    op.add_column('contacts', sa.Column('email', sa.String(), nullable=False, index=True))
    op.add_column('contacts', sa.Column('phone_number', sa.String(), nullable=True))
    
    # Data migration: decrypt existing emails and phone numbers
    op.execute("""
        UPDATE contacts SET email = _email;
    """)
    op.execute("""
        UPDATE contacts SET phone_number = _phone_number WHERE _phone_number IS NOT NULL;
    """)
    
    # Drop encrypted columns
    op.drop_column('contacts', '_email')
    op.drop_column('contacts', '_phone_number')
    
    # Drop indexes
    op.drop_index('ix_contacts_tags', table_name='contacts')
    op.drop_index('ix_contacts_search_vector', table_name='contacts')
    
    # Drop new columns
    op.drop_column('contacts', 'deleted_at')
    op.drop_column('contacts', 'search_vector')
