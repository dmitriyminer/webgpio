"""create tables

Revision ID: eff453bf5960
Revises: 
Create Date: 2016-12-25 01:18:25.912212

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eff453bf5960'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('is_superuser', sa.Boolean, nullable=False,
                  server_default='FALSE'),
        sa.Column('passwd', sa.String(256), nullable=False),
    )

    op.create_table(
        'devices',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'),
                  nullable=False)
    )

    op.create_table(
        'ports',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('gpio', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.Boolean(), nullable=False),
        sa.Column('device_id',
                  sa.Integer,
                  sa.ForeignKey('devices.id', ondelete='CASCADE',
                                onupdate='CASCADE'),
                  nullable=False)
    )


def downgrade():
    op.drop_table('users')
    op.drop_table('devices')
    op.drop_table('ports')
