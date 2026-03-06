"""
tests/test_email_factory.py

Unit tests for email_factory.EmailFactory.email_constructor.
Tests the six email format variants and edge cases.
"""
import pytest
from email_factory import EmailFactory


class TestEmailConstructorBasic:
    """Standard two-word names should produce exactly six email variants."""

    def setup_method(self):
        self.result = EmailFactory.email_constructor('John Doe', 'uber')

    def test_returns_six_variants(self):
        assert len(self.result) == 6

    def test_first_name_only(self):
        assert 'john@uber.com' in self.result

    def test_last_name_only(self):
        assert 'doe@uber.com' in self.result

    def test_first_plus_last(self):
        assert 'johndoe@uber.com' in self.result

    def test_first_plus_last_initial(self):
        assert 'johnd@uber.com' in self.result

    def test_last_plus_first_initial(self):
        assert 'doej@uber.com' in self.result

    def test_first_initial_plus_last(self):
        assert 'jdoe@uber.com' in self.result

    def test_all_lowercase(self):
        for email in self.result:
            local, domain = email.split('@')
            assert local == local.lower()

    def test_correct_domain(self):
        for email in self.result:
            assert email.endswith('@uber.com')


class TestEmailConstructorEdgeCases:
    def test_name_with_parentheses_returns_none(self):
        assert EmailFactory.email_constructor('John (Doe)', 'uber') is None

    def test_name_with_only_open_paren_returns_none(self):
        assert EmailFactory.email_constructor('John (Doe', 'uber') is None

    def test_name_with_only_close_paren_returns_none(self):
        assert EmailFactory.email_constructor('John Doe)', 'uber') is None

    def test_mixed_case_name_lowercased(self):
        result = EmailFactory.email_constructor('JOHN DOE', 'uber')
        assert all(e == e.lower() for e in result)

    def test_three_word_name_uses_first_and_last(self):
        """Middle names should be ignored — first and last token used."""
        result = EmailFactory.email_constructor('John Michael Doe', 'uber')
        assert result is not None
        # first = 'john', last = 'doe'
        assert 'john@uber.com' in result
        assert 'doe@uber.com' in result
        assert 'johndoe@uber.com' in result

    def test_custom_domain(self):
        result = EmailFactory.email_constructor('Jane Smith', 'example')
        assert all('@example.com' in e for e in result)

    def test_returns_list_type(self):
        result = EmailFactory.email_constructor('Jane Smith', 'uber')
        assert isinstance(result, list)

    def test_no_duplicates_for_simple_name(self):
        result = EmailFactory.email_constructor('Al Bo', 'uber')
        assert len(result) == len(set(result))


class TestEmailConstructorFormatConsistency:
    """Verify format rules hold for a variety of names."""

    @pytest.mark.parametrize("name,expected_formats", [
        ('Alice Wong', ['alice@uber.com', 'wong@uber.com', 'alicewong@uber.com',
                        'alicew@uber.com', 'wonga@uber.com', 'awong@uber.com']),
        ('Bob Li', ['bob@uber.com', 'li@uber.com', 'bobli@uber.com',
                    'bobl@uber.com', 'lib@uber.com', 'bli@uber.com']),
    ])
    def test_parametrized_formats(self, name, expected_formats):
        result = EmailFactory.email_constructor(name, 'uber')
        assert set(result) == set(expected_formats)
