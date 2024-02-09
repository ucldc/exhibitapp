from django.template import Library
import markdown
from markdown.extensions import Extension

# https://github.com/Python-Markdown/markdown/commit/7db56daedf8a6006222f55eeeab748e7789fba89 
# per notes in the release docs for version 2.5, used an EscapeHTML 
# extension to replace safe_mode="escape" (deprecated)

# https://python-markdown.github.io/changelog/#safe_mode-and-html_replacement_text-keywords-deprecated
# https://python-markdown.github.io/changelog/#md_globals-keyword-deprecated-from-extension-api
# https://python-markdown.github.io/changelog/#previously-deprecated-objects-have-been-removed

class EscapeHtml(Extension):
	def extendMarkdown(self, md):
		md.preprocessors.deregister('html_block')
		md.inlinePatterns.deregister('html')

register = Library()

@register.filter
def markdownify(text):
    return markdown.markdown(text,extensions=[EscapeHtml()])