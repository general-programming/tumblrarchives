# This Python file uses the following encoding: utf-8
import re
from paginate import make_html_tag
from paginate_sqlalchemy import SqlalchemyOrmPage


# Pagination class credit https://github.com/ckan/ckan/blob/fd4d60c64a28801ed1dea76f353f8f6ee9f74d45/ckan/lib/helpers.py#L890-L925

class Page(SqlalchemyOrmPage):
    # Put each page link into a <li> (for Bootstrap to style it)

    @staticmethod
    def default_link_tag(item, extra_attributes=None):
        """
        Create an A-HREF tag that points to another page.
        """
        extra_attributes = extra_attributes or {}

        text = item["value"]
        target_url = item["href"]

        a_html = make_html_tag("a", text=text, href=target_url, **item["attrs"])
        return make_html_tag("li", a_html, **extra_attributes)

    # Curry the pager method of the webhelpers.paginate.Page class, so we have
    # our custom layout set as default.

    def pager(self, *args, **kwargs):
        kwargs.update(
            format='<ul class="pagination">$link_previous ~2~ $link_next</ul></nav>',
            symbol_previous='«',
            symbol_next='»',
            dotdot_attr={'class': 'pager_dotdot'},
            curpage_attr={'class': 'active waves-effect'},
            link_attr={'class': 'waves-effect'}
        )
        return super(Page, self).pager(*args, **kwargs)

    # Change 'current page' link from <span> to <li><a>
    # and '..' into '<li><a>..'
    # (for Bootstrap to style them properly)

    def _range(self, link_map, radius):
        html = super(Page, self)._range(link_map, radius)
        # Convert ..
        dotdot = '<span class="pager_dotdot">..</span>'
        html = re.sub(dotdot, "", html)

        return html
