"""Tumblr post id

Revision ID: fb2349f5aa64
Revises: 5b6096b0b7b2
Create Date: 2018-12-08 00:37:18.920234

"""

# revision identifiers, used by Alembic.
revision = 'fb2349f5aa64'
down_revision = '5b6096b0b7b2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


from archives.lib.model import Post, sm


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('tumblr_id', sa.BigInteger(), nullable=True))
    # ### end Alembic commands ###

    # Force commit the operation
    conn = op.get_bind()
    conn.execute("COMMIT")

    updates = []
    added = 0
    db = sm()
    commit_db = sm()

    for post in db.query(Post).filter(sa.or_(
        Post.data.has_key("id"),
    )).yield_per(512):
        try:
            new_data = post.data.copy()
            tumblr_id = new_data.pop("id")

            updates.append({
                "id": post.id,
                "tumblr_id": tumblr_id,
                "data": new_data
            })
        except KeyError:
            continue
        
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
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'tumblr_id')
    # ### end Alembic commands ###
