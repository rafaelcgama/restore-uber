import logging

logger = logging.getLogger(__name__)


class EmailFactory:
    """
    Constructs all plausible email address variants for a given name and domain.

    LinkedIn names sometimes include suffixes like "(MBA)" that would produce
    invalid email addresses — these are detected and skipped.
    """

    @staticmethod
    def email_constructor(name: str, domain: str) -> list[str] | None:
        """
        Generate up to six email format variants for ``name`` at ``domain``.

        Returns ``None`` if the name contains parentheses (e.g. credentials
        like "John Doe (MBA)"), as these cannot be safely split into a
        first/last name.

        Formats generated for **John Doe** at **uber**:

        =====================  ========================
        Format                 Example
        =====================  ========================
        First only             ``john@uber.com``
        Last only              ``doe@uber.com``
        First + last           ``johndoe@uber.com``
        First + last initial   ``johnd@uber.com``
        Last + first initial   ``doej@uber.com``
        First initial + last   ``jdoe@uber.com``
        =====================  ========================

        :param name: Full name as scraped from LinkedIn.
        :param domain: Company domain without TLD (e.g. ``'uber'``).
        :return: List of six email strings, or ``None`` if the name is unusable.
        """
        if '(' in name or ')' in name:
            logger.debug(f'Skipping name with parentheses: "{name}"')
            return None

        parts = name.split()
        first = parts[0].lower()
        last = parts[-1].lower()

        emails = [
            f'{first}@{domain}.com',
            f'{last}@{domain}.com',
            f'{first}{last}@{domain}.com',
            f'{first}{last[0]}@{domain}.com',
            f'{last}{first[0]}@{domain}.com',
            f'{first[0]}{last}@{domain}.com',
        ]

        logger.debug(f'Constructed {len(emails)} email variants for "{name}" @ {domain}.com')
        return emails
