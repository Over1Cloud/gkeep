"""Add is_archived field to Note model

Revision ID: 785679004e8b
Revises: b4d5b1cafe95
Create Date: 2024-10-20 18:19:33.460479

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '785679004e8b'
down_revision = 'b4d5b1cafe95'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('note', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_archived', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('note', schema=None) as batch_op:
        batch_op.drop_column('is_archived')

    # ### end Alembic commands ###
