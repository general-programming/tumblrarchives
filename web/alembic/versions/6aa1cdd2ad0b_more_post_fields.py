"""more post fields

Revision ID: 6aa1cdd2ad0b
Revises: fb2349f5aa64
Create Date: 2018-12-08 00:59:04.176829

"""

# revision identifiers, used by Alembic.
revision = '6aa1cdd2ad0b'
down_revision = 'fb2349f5aa64'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

import datetime

from archives.lib.model import Post, sm

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.add_column('posts', sa.Column('format', sa.String(), nullable=True))
    # op.add_column('posts', sa.Column('note_count', sa.Integer(), nullable=True))
    # op.add_column('posts', sa.Column('posted', sa.DateTime(), nullable=True))
    # op.add_column('posts', sa.Column('reblog_key', sa.String(), nullable=True))
    # ### end Alembic commands ###

    # Force commit the operation
    conn = op.get_bind()
    conn.execute("COMMIT")

    updates = []
    added = 0
    db = sm()
    commit_db = sm()

    for post in db.query(Post).filter(sa.or_(
        Post.data.has_key("format"),
        Post.data.has_key("note_count"),
        Post.data.has_key("timestamp"),
        Post.data.has_key("reblog_key"),
    )).yield_per(512):
        try:
            new_data = post.data.copy()

            # Post time
            new_data.pop("date", None)
            post_epoch = new_data.pop("timestamp", 0)
            post_time = max(
                datetime.datetime.fromtimestamp(post_epoch),
                post.posted or datetime.datetime.fromtimestamp(post_epoch)
            )

            # Other fields
            post_format = new_data.pop("format", post.format)
            post_note_count = max(
                post.note_count or 0,
                new_data.pop("note_count", 0)
            )
            post_reblog_key = new_data.pop("reblog_key", post.reblog_key)

            updates.append({
                "id": post.id,
                "posted": post_time,
                "note_count": post_note_count,
                "reblog_key": post_reblog_key,
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
    op.drop_column('posts', 'reblog_key')
    op.drop_column('posts', 'posted')
    op.drop_column('posts', 'note_count')
    op.drop_column('posts', 'format')
    # ### end Alembic commands ###