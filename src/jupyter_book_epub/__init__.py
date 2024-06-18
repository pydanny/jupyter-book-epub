import logging
from os import path
from typing import Any

from sphinx.builders import epub3
from sphinx.util.fileutil import copy_asset_file
from sphinx.locale import __



logger = logging.getLogger(__name__)


class JupyterBookEpubBuilder(epub3.Epub3Builder):
    name = 'jupyter_book_epub'
    format = 'epub'

    def build_toc(self) -> None:
        """Write the metainfo file toc.ncx.
            
            Note: This removes some of the filtering logic of the parent class
            to ensure the toc.ncx file is built properly.
        
        """
        logger.info(__('writing toc.ncx file...'))

        refnodes = self.refnodes
        self.check_refnodes(refnodes)
        navpoints = self.build_navpoints(refnodes)
        level = max(item['level'] for item in self.refnodes)
        level = min(level, self.config.epub_tocdepth)
        copy_asset_file(path.join(self.template_dir, 'toc.ncx_t'), self.outdir,
                        self.toc_metadata(level, navpoints))
        
    def build_navlist(self, navnodes: list[dict[str, Any]]) -> list[epub3.NavPoint]:
        """Create the toc navigation structure.

        This method is almost same as build_navpoints method in epub.py.
        This is because the logical navigation structure of epub3 is not
        different from one of epub2.

        The difference from build_navpoints method is templates which are used
        when generating navigation documents.
        """
        navstack: list[epub3.NavPoint] = []
        navstack.append(epub3.NavPoint('', '', []))
        level = 0
        for node in navnodes:
            if not node['text']:
                continue
            file = node['refuri'].split('#')[0]
            if file in self.ignored_files:
                continue
            if node['level'] > self.config.epub_tocdepth:
                continue

            navpoint = epub3.NavPoint(node['text'], node['refuri'], [])
            if node['level'] == level:
                navstack.pop()
                navstack[-1].children.append(navpoint)
                navstack.append(navpoint)
            elif node['level'] == level + 1:
                level += 1
                navstack[-1].children.append(navpoint)
                navstack.append(navpoint)
            elif node['level'] < level:
                while node['level'] < len(navstack):
                    navstack.pop()
                level = node['level']
                navstack[-1].children.append(navpoint)
                navstack.append(navpoint)
            else:
                unreachable = 'Should never reach here. It might be a bug.'
                raise RuntimeError(unreachable)

        return navstack[0].children
        
    def build_navigation_doc(self) -> None:
        """Write the metainfo file nav.xhtml.
        
            Note: This removes some of the filtering logic in the parent class
            to ensure the nav.xhtml file is built properly.        
        """
        logger.info(__('writing nav.xhtml file...'))
        refnodes = self.refnodes
        navlist = self.build_navlist(refnodes)
        copy_asset_file(path.join(self.template_dir, 'nav.xhtml_t'), self.outdir,
                        self.navigation_doc_metadata(navlist))

        # Add nav.xhtml to epub file
        if 'nav.xhtml' not in self.files:
            self.files.append('nav.xhtml')


def setup(app):
    app.add_builder(JupyterBookEpubBuilder)