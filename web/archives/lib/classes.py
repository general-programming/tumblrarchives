# This Python file uses the following encoding: utf-8
import re
from paginate import make_html_tag
from paginate_sqlalchemy import SqlalchemyOrmPage


# Pagination class credit https://github.com/ckan/ckan/blob/fd4d60c64a28801ed1dea76f353f8f6ee9f74d45/ckan/lib/helpers.py#L890-L925

class Page(SqlalchemyOrmPage):
    # Curry the pager method of the webhelpers.paginate.Page class, so we have
    # our custom layout set as default.

    def pager(self, *args, **kwargs):
        kwargs.update(
            format='<ul class="pagination">$link_previous ~2~ $link_next</ul></nav>',
            symbol_previous='«',
            symbol_next='»',
            curpage_attr={'class': 'active waves-effect'},
            link_attr={'class': 'waves-effect'}
        )
        return super(Page, self).pager(*args, **kwargs)

    # Put each page link into a <li> (for Bootstrap to style it)

    def _pagerlink(self, page, text, extra_attributes=None):
        anchor = super(Page, self)._pagerlink(page, text)
        extra_attributes = extra_attributes or {}
        return make_html_tag("li", anchor, **extra_attributes)

    # Change 'current page' link from <span> to <li><a>
    # and '..' into '<li><a>..'
    # (for Bootstrap to style them properly)

    def _range(self, regexp_match):
        html = super(Page, self)._range(regexp_match)
        # Convert ..
        dotdot = '<span class="pager_dotdot">..</span>'
        html = re.sub(dotdot, "", html)

        # Convert current page
        text = '%s' % self.page
        current_page_span = str(make_html_tag("span", text, **self.curpage_attr))
        current_page_link = self._pagerlink(self.page, text,
                                            extra_attributes=self.curpage_attr)
        return re.sub(current_page_span, current_page_link, html)
