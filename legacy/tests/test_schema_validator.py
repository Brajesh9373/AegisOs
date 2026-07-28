import pytest

from ecms.core.schema_validator import validate_relationship
from ecms.core.uko import UKOType


class TestValidateRelationship:
    def test_valid_containment(self) -> None:
        is_valid, reason = validate_relationship("contained_in", UKOType.FILE)
        assert is_valid, reason
        is_valid, _ = validate_relationship("contained_in", UKOType.DOCUMENT)
        assert is_valid

    def test_invalid_containment(self) -> None:
        is_valid, reason = validate_relationship("contained_in", UKOType.PERSON)
        assert not is_valid
        assert "contained_in" in reason

    def test_valid_defined_in(self) -> None:
        is_valid, _ = validate_relationship("defined_in", UKOType.CLASS)
        assert is_valid

    def test_invalid_defined_in(self) -> None:
        is_valid, reason = validate_relationship("defined_in", UKOType.FUNCTION)
        assert not is_valid

    def test_valid_belongs_to(self) -> None:
        is_valid, _ = validate_relationship("belongs_to", UKOType.TABLE)
        assert is_valid

    def test_invalid_belongs_to(self) -> None:
        is_valid, reason = validate_relationship("belongs_to", UKOType.FUNCTION)
        assert not is_valid

    def test_unknown_relationship(self) -> None:
        is_valid, reason = validate_relationship("fictional_edge", UKOType.FILE)
        assert not is_valid
        assert "Unknown" in reason

    def test_changed_accepts_all_types(self) -> None:
        for uko_type in UKOType:
            is_valid, reason = validate_relationship("changed", uko_type)
            assert is_valid, f"changed should accept {uko_type.value}: {reason}"

    def test_same_as_only_person_or_name(self) -> None:
        assert validate_relationship("same_as", UKOType.PERSON)[0]
        assert validate_relationship("same_as", UKOType.NAME)[0]
        assert not validate_relationship("same_as", UKOType.FILE)[0]

    def test_authored_by_only_person_or_name(self) -> None:
        assert validate_relationship("authored_by", UKOType.PERSON)[0]
        assert validate_relationship("authored_by", UKOType.NAME)[0]
        assert not validate_relationship("authored_by", UKOType.CLASS)[0]

    def test_extracted_from_valid_targets(self) -> None:
        valid = {UKOType.FILE, UKOType.DOCUMENT, UKOType.MESSAGE, UKOType.TICKET,
                 UKOType.COMMIT, UKOType.FUNCTION, UKOType.CLASS}
        for t in valid:
            assert validate_relationship("extracted_from", t)[0], f"extracted_from should accept {t.value}"
        assert not validate_relationship("extracted_from", UKOType.PERSON)[0]
