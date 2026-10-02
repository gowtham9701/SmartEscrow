"""
Unit tests for the arbitration majority-vote tallying logic.
"""
import pytest

from app.services.arbitration_service import ArbitrationService
from app.models.entities import VoteDecision


def test_generate_anonymized_ticket_ref_is_unique_and_hex():
    ref1 = ArbitrationService.generate_anonymized_ticket_ref()
    ref2 = ArbitrationService.generate_anonymized_ticket_ref()
    assert ref1 != ref2
    assert len(ref1) == 32
    int(ref1, 16)  # must be valid hex
