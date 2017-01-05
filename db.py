import sqlalchemy as sa


metadata = sa.MetaData()

users = sa.Table(
    'users', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('email', sa.String(255), nullable=False),
    sa.Column('passwd', sa.String(256), nullable=False),
    sa.Column('is_superuser', sa.Boolean, nullable=False,
              server_default='FALSE'),
)

devices = sa.Table(
    'devices', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('key', sa.String(255), nullable=False),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False)
)

ports = sa.Table(
    'ports', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('gpio', sa.Integer, nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('status', sa.Boolean(), nullable=False),
    sa.Column('device_id',
              sa.Integer,
              sa.ForeignKey('devices.id', ondelete='CASCADE',
                            onupdate='CASCADE'),
              nullable=False)
)
