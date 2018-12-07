"""link posts with blog objects

Revision ID: 1e5f23d15ea3
Revises: 74ca131663c0
Create Date: 2018-12-07 09:56:38.838460

"""

# revision identifiers, used by Alembic.
revision = '1e5f23d15ea3'
down_revision = '74ca131663c0'
branch_labels = None
depends_on = None

import sys
from alembic import op
import sqlalchemy as sa
from archives.lib.model import sm, Post, Blog

blogs = {}

def get_blog(db, name):
    if name in blogs:
        return blogs[name]

    blog = db.query(Blog).filter(Blog.name == name).scalar()
    if not blog:
        print("Creating placeholder entry for URL " + name)
        blog = Blog(
            url=name + ".tumblr.com",
            name=name,
            tumblr_uid="unknown:" + name,
            data={}
        )
        db.add(blog)
        db.commit()

    blogs[name] = blog
    return blogs[name]

def upgrade():
    db = sm()
    for post in db.query(Post):
        blog = get_blog(db, post.url)
        post.author = blog.id
        sys.stdout.write(".")
    sys.stdout.write("\nCommiting.\n")
    db.commit()


def downgrade():
    pass
