"""Initial schema

Revision ID: 479afe9eabfe
Revises: 
Create Date: 2025-05-29 08:53:42.160629

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '479afe9eabfe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('avatar', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_full_name'), 'user', ['full_name'], unique=False)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_table('analysis_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('product_id', sa.String(), nullable=False),
    sa.Column('marketplace', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('max_reviews', sa.Integer(), nullable=True),
    sa.Column('is_processed', sa.Boolean(), nullable=True),
    sa.Column('error', sa.String(), nullable=True),
    sa.Column('progress_percentage', sa.Float(), nullable=True),
    sa.Column('current_stage', sa.String(), nullable=True),
    sa.Column('processed_reviews', sa.Integer(), nullable=True),
    sa.Column('total_reviews', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_requests_id'), 'analysis_requests', ['id'], unique=False)
    op.create_table('analysis_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=True),
    sa.Column('positive_aspects', sa.JSON(), nullable=True),
    sa.Column('negative_aspects', sa.JSON(), nullable=True),
    sa.Column('aspect_categories', sa.JSON(), nullable=True),
    sa.Column('reviews_count', sa.Integer(), nullable=True),
    sa.Column('sentiment_summary', sa.JSON(), nullable=True),
    sa.Column('product_info', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['request_id'], ['analysis_requests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_results_id'), 'analysis_results', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_analysis_results_id'), table_name='analysis_results')
    op.drop_table('analysis_results')
    op.drop_index(op.f('ix_analysis_requests_id'), table_name='analysis_requests')
    op.drop_table('analysis_requests')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_full_name'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ### 