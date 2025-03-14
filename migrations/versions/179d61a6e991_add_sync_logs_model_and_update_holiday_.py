"""Add sync_logs model and update holiday model

Revision ID: 179d61a6e991
Revises: a71df35a51e5
Create Date: 2025-03-09 13:28:48.603050

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '179d61a6e991'
down_revision = 'a71df35a51e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('holidays', sa.Column('holiday_date', sa.Date(), nullable=False))
    op.add_column('holidays', sa.Column('is_national_holiday', sa.Boolean(), nullable=True))
    op.add_column('holidays', sa.Column('is_repeating_yearly', sa.Boolean(), nullable=True))
    op.add_column('holidays', sa.Column('region_id', sa.Integer(), nullable=True))
    op.add_column('holidays', sa.Column('original_id', sa.String(length=50), nullable=True))
    op.drop_index('ix_holidays_date', table_name='holidays')
    op.create_index(op.f('ix_holidays_holiday_date'), 'holidays', ['holiday_date'], unique=True)
    op.create_foreign_key(None, 'holidays', 'regions', ['region_id'], ['id'])
    op.drop_column('holidays', 'date')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('holidays', sa.Column('date', sa.DATE(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'holidays', type_='foreignkey')
    op.drop_index(op.f('ix_holidays_holiday_date'), table_name='holidays')
    op.create_index('ix_holidays_date', 'holidays', ['date'], unique=True)
    op.drop_column('holidays', 'original_id')
    op.drop_column('holidays', 'region_id')
    op.drop_column('holidays', 'is_repeating_yearly')
    op.drop_column('holidays', 'is_national_holiday')
    op.drop_column('holidays', 'holiday_date')
    # ### end Alembic commands ### 