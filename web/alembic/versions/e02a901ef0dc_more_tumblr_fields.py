"""more tumblr fields

Revision ID: e02a901ef0dc
Revises: 9dafd4fd2d5f
Create Date: 2018-12-08 09:30:46.344973

"""

# revision identifiers, used by Alembic.
revision = 'e02a901ef0dc'
down_revision = '9dafd4fd2d5f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from archives.lib.model import Post, PostMeta, sm


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('posts_meta',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('can_like', sa.Boolean(), server_default='t', nullable=True),
    sa.Column('can_reblog', sa.Boolean(), server_default='t', nullable=True),
    sa.Column('can_reply', sa.Boolean(), server_default='t', nullable=True),
    sa.Column('display_avatar', sa.Boolean(), server_default='t', nullable=True),
    sa.Column('is_blocks_post_format', sa.Boolean(), server_default='f', nullable=True),
    sa.Column('can_send_in_message', sa.Boolean(), server_default='t', nullable=True),
    sa.Column('post_url', sa.String(), nullable=True),
    sa.Column('short_url', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['posts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # op.add_column('posts', sa.Column('slug', sa.Unicode(), nullable=True))
    # op.add_column('posts', sa.Column('state', sa.String(), nullable=True))
    # op.add_column('posts', sa.Column('summary', sa.Unicode(), nullable=True))
    # ### end Alembic commands ###

    # Force commit the operation
    conn = op.get_bind()
    conn.execute("COMMIT")

    updates = []
    added = 0
    db = sm()
    commit_db = sm()

    for post in db.query(Post).filter(sa.or_(
        Post.data.has_key("slug"),
        Post.data.has_key("state"),
        Post.data.has_key("summary"),
        Post.data.has_key("liked")
    )).yield_per(512):
        new_data = post.data.copy()

        update = {
            "id": post.id,
            "data": new_data
        }

        update["slug"] = new_data.pop("slug", post.slug)
        update["state"] = new_data.pop("state", post.state)
        update["summary"] = new_data.pop("summary", post.summary)
        post_meta = PostMeta.create_from_metadata(commit_db, new_data, post.id)

        updates.append(update)
        
        # Commit every 512 posts.
        added += 1
        if len(updates) == 512:
            commit_db.execute("SET synchronous_commit TO off")
            print(f"{added} posts processed.", flush=True)
            commit_db.bulk_update_mappings(Post, updates)
            commit_db.commit()
            updates.clear()

    if updates:
        commit_db.bulk_update_mappings(Post, updates)
        commit_db.commit()

def downgrade():
    pass