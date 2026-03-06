"""
tests/test_data_cleaning.py

Unit tests for data_cleaning:
  - Conditions.meet_conditions() — the filtering predicate
  - clean_data() — the full cleaning pipeline

All tests are pure-Python; no network or filesystem access required.
"""
import pytest
from data_cleaning import clean_data
from data_cleaning.data_cleaning import Conditions


# ── Conditions.meet_conditions ─────────────────────────────────────────────────

class TestConditionsMeetConditions:
    """Test the individual filtering predicate."""

    # ── Should PASS (meet_conditions → True) ──────────────────────────────────

    @pytest.mark.parametrize("position", [
        "Software Engineer at Uber",
        "Senior Product Manager, Uber",
        "Data Scientist - Uber",
        "Uber Eats waitress",
        # "Eats" alone without "Uber Eats" doesn't match — product filter only checks "uber air", "freight", "elevate"
    ])
    def test_valid_uber_positions_pass(self, position):
        assert Conditions.meet_conditions(position) is True

    # ── Should FAIL (meet_conditions → False) ─────────────────────────────────

    @pytest.mark.parametrize("position", [
        "Ex-Uber Engineer",
        "ex-uber developer",
        "Software Engineer",  # No "uber" in position → treated as former employee
        "works at Google",
        "Driver at Uber",
        "Motorista Uber",  # Portuguese driver term
        "Uber Air Engineer",
        "UberAir Operations",
        "Freight Manager at Uber",
        "Elevate Product Lead",
    ])
    def test_invalid_positions_filtered(self, position):
        assert Conditions.meet_conditions(position) is False

    def test_case_insensitive_filtering(self):
        assert Conditions.meet_conditions("EX-UBER ENGINEER") is False
        assert Conditions.meet_conditions("DRIVER at Uber") is False
        assert Conditions.meet_conditions("Uber FREIGHT Lead") is False

    def test_uber_eats_is_not_filtered(self):
        """'Uber Eats' is NOT in the excluded list — only uber air, freight, elevate are."""
        assert Conditions.meet_conditions("Uber Eats Delivery Operations") is True


# ── clean_data ─────────────────────────────────────────────────────────────────

class TestCleanData:
    """Test the full clean_data pipeline."""

    def test_removes_linkedin_member_placeholder(self):
        data = [{'name': 'LinkedIn Member', 'position': 'Software Engineer at Uber'}]
        assert clean_data(data) == []

    def test_case_insensitive_linkedin_member(self):
        data = [{'name': 'linkedin member', 'position': 'Engineer at Uber'}]
        assert clean_data(data) == []

    def test_keeps_valid_employee(self):
        employee = {'name': 'Jane Doe', 'position': 'Product Manager at Uber'}
        result = clean_data([employee])
        assert result == [employee]

    def test_removes_former_employee(self):
        data = [{'name': 'John Smith', 'position': 'ex-uber engineer'}]
        assert clean_data(data) == []

    def test_removes_driver(self):
        data = [{'name': 'Carlos Silva', 'position': 'Motorista Uber'}]
        assert clean_data(data) == []

    def test_removes_uber_air(self):
        data = [{'name': 'Alice Wu', 'position': 'Uber Air Operations Manager'}]
        assert clean_data(data) == []

    def test_removes_freight(self):
        data = [{'name': 'Bob Lee', 'position': 'Freight Analyst at Uber'}]
        assert clean_data(data) == []

    def test_removes_elevate(self):
        data = [{'name': 'Sara Kim', 'position': 'Elevate Product Lead at Uber'}]
        assert clean_data(data) == []

    def test_empty_input_returns_empty(self):
        assert clean_data([]) == []

    def test_mixed_list_filters_correctly(self):
        data = [
            {'name': 'Valid Employee', 'position': 'Engineer at Uber'},
            {'name': 'LinkedIn Member', 'position': 'Software Engineer at Uber'},
            {'name': 'Former Worker', 'position': 'ex-uber engineer'},
            {'name': 'Good Engineer', 'position': 'Senior SWE Uber'},
        ]
        result = clean_data(data)
        names = [e['name'] for e in result]
        assert 'Valid Employee' in names
        assert 'Good Engineer' in names
        assert 'LinkedIn Member' not in names
        assert 'Former Worker' not in names

    def test_all_invalid_returns_empty(self):
        data = [
            {'name': 'LinkedIn Member', 'position': 'anything'},
            {'name': 'John', 'position': 'ex-uber engineer'},
            {'name': 'Jane', 'position': 'Driver at Uber'},
        ]
        assert clean_data(data) == []

    def test_preserves_employee_dict_structure(self):
        """clean_data should not mutate or reformat the dicts it keeps."""
        employee = {'name': 'Test User', 'position': 'PM at Uber'}
        result = clean_data([employee])
        assert result[0] is employee  # same object, not a copy

    def test_large_list_performance(self):
        """Should handle hundreds of records without issue."""
        data = [{'name': f'Employee {i}', 'position': 'Engineer at Uber'} for i in range(500)]
        result = clean_data(data)
        assert len(result) == 500
