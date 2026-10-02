# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from jinja2 import TemplateNotFound, UndefinedError

from tol.notify import TemplateRenderer


@pytest.fixture
def app_dir(tmp_path):
    """An app template dir containing a 'welcome' email."""
    (tmp_path / 'welcome.subject.txt').write_text('Welcome, {{name}}\n')
    (tmp_path / 'welcome.body.html').write_text(
        '{% extends "tol_base.html" %}'
        '{% block content %}<p>Hello {{name}}</p>{% endblock %}'
    )
    return tmp_path


@pytest.fixture
def renderer(app_dir):
    """A renderer searching app_dir, then SDK templates."""
    return TemplateRenderer([app_dir])


class TestRenderer:
    def test_subject_and_body(self, renderer):
        """Test that both templates render with the context."""
        subject, html = renderer.render('welcome', {'name': 'Lucas'})

        assert subject == 'Welcome, Lucas'
        assert '<p>Hello Lucas</p>' in html

    def test_extends_sdk_base(self, renderer):
        """Test that app templates can extend the SDK's tol_base.html."""
        _, html = renderer.render('welcome', {'name': 'Lucas'})

        assert 'Wellcome Sanger Institute' in html

    def test_app_base_shadows_sdk_base(self, app_dir, renderer):
        """Test that an app's tol_base.html wins over the SDK's."""
        (app_dir / 'tol_base.html').write_text(
            '<main>{% block content %}{% endblock %}</main>'
        )

        _, html = renderer.render('welcome', {'name': 'Lucas'})

        assert html == '<main><p>Hello Lucas</p></main>'


class TestEscaping:
    def test_html_context_is_escaped(self, renderer):
        """Test that user data cannot inject markup into the body."""
        _, html = renderer.render('welcome', {'name': '<script>x</script>'})

        assert '<script>' not in html
        assert '&lt;script&gt;' in html

    def test_subject_is_not_escaped(self, renderer):
        """Test that the plain-text subject is not HTML-escaped."""
        subject, _ = renderer.render('welcome', {'name': 'Me & You'})

        assert subject == 'Welcome, Me & You'

    def test_subject_newlines_collapsed(self, renderer):
        """Test that newlines from context cannot reach the header."""
        subject, _ = renderer.render(
            'welcome', {'name': 'BadBoy111\r\nBcc: evil@example.com'}
        )

        assert subject == 'Welcome, BadBoy111 Bcc: evil@example.com'


class TestErrors:
    def test_missing_variable_raises(self, renderer):
        """Test that a missing context value fails instead of rendering ''."""
        with pytest.raises(UndefinedError):
            renderer.render('welcome', {})

    def test_missing_template_raises(self, renderer):
        """Test that an unknown notification type fails loudly."""
        with pytest.raises(TemplateNotFound):
            renderer.render('nope', {})

    def test_single_path_rejected(self, app_dir):
        """Test that a bare string is not iterated char-by-char."""
        with pytest.raises(TypeError):
            TemplateRenderer(str(app_dir))
