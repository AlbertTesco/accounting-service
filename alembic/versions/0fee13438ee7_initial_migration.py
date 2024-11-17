"""Initial migration

Revision ID: 0fee13438ee7
Revises: 
Create Date: 2024-11-17 11:54:03.216316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fee13438ee7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('employees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('rank', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_employees_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_employees_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_employees_rank'), ['rank'], unique=False)

    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_projects_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_projects_name'), ['name'], unique=False)

    op.create_table('employee_project_assignments',
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('employee_id', 'project_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('employee_project_assignments')
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_projects_name'))
        batch_op.drop_index(batch_op.f('ix_projects_id'))

    op.drop_table('projects')
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_employees_rank'))
        batch_op.drop_index(batch_op.f('ix_employees_name'))
        batch_op.drop_index(batch_op.f('ix_employees_id'))

    op.drop_table('employees')
    # ### end Alembic commands ###
