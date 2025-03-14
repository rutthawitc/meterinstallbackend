"""Make installation request fields nullable

Revision ID: 56ab5caed48c
Revises: ded5fcdce8bd
Create Date: 2025-03-10 16:28:05.567708

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '56ab5caed48c'
down_revision = 'ded5fcdce8bd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('installation_requests', 'request_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.drop_constraint('installation_requests_customer_id_fkey', 'installation_requests', type_='foreignkey')
    op.drop_constraint('installation_requests_meter_size_id_fkey', 'installation_requests', type_='foreignkey')
    op.drop_constraint('installation_requests_branch_code_fkey', 'installation_requests', type_='foreignkey')
    op.drop_constraint('installation_requests_status_id_fkey', 'installation_requests', type_='foreignkey')
    op.drop_constraint('installation_requests_installation_type_id_fkey', 'installation_requests', type_='foreignkey')
    op.drop_constraint('installation_requests_created_by_fkey', 'installation_requests', type_='foreignkey')
    op.create_foreign_key(None, 'installation_requests', 'branches', ['branch_code'], ['ba_code'], ondelete='SET NULL')
    op.create_foreign_key(None, 'installation_requests', 'installation_statuses', ['status_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'installation_requests', 'installation_types', ['installation_type_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'installation_requests', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'installation_requests', 'customers', ['customer_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'installation_requests', 'meter_sizes', ['meter_size_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'installation_requests', type_='foreignkey')
    op.drop_constraint(None, 'installation_requests', type_='foreignkey')
    op.drop_constraint(None, 'installation_requests', type_='foreignkey')
    op.drop_constraint(None, 'installation_requests', type_='foreignkey')
    op.drop_constraint(None, 'installation_requests', type_='foreignkey')
    op.drop_constraint(None, 'installation_requests', type_='foreignkey')
    op.create_foreign_key('installation_requests_created_by_fkey', 'installation_requests', 'users', ['created_by'], ['id'])
    op.create_foreign_key('installation_requests_installation_type_id_fkey', 'installation_requests', 'installation_types', ['installation_type_id'], ['id'])
    op.create_foreign_key('installation_requests_status_id_fkey', 'installation_requests', 'installation_statuses', ['status_id'], ['id'])
    op.create_foreign_key('installation_requests_branch_code_fkey', 'installation_requests', 'branches', ['branch_code'], ['ba_code'])
    op.create_foreign_key('installation_requests_meter_size_id_fkey', 'installation_requests', 'meter_sizes', ['meter_size_id'], ['id'])
    op.create_foreign_key('installation_requests_customer_id_fkey', 'installation_requests', 'customers', ['customer_id'], ['id'])
    op.alter_column('installation_requests', 'request_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    # ### end Alembic commands ### 