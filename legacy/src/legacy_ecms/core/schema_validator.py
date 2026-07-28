from legacy_ecms.core.uko import UKOType


VALID_RELATIONSHIP_TARGETS: dict[str, set[UKOType]] = {
    "contained_in": {UKOType.FILE, UKOType.DOCUMENT},
    "defined_in": {UKOType.CLASS},
    "extends": {UKOType.CLASS},
    "calls": {UKOType.FUNCTION, UKOType.API},
    "uses_import": {UKOType.IMPORT},
    "defines_method": {UKOType.FUNCTION},
    "belongs_to": {UKOType.TABLE},
    "references": {UKOType.TABLE},
    "extracted_from": {
        UKOType.FILE, UKOType.DOCUMENT, UKOType.MESSAGE,
        UKOType.TICKET, UKOType.COMMIT, UKOType.FUNCTION, UKOType.CLASS,
    },
    "supported_by": {
        UKOType.FILE, UKOType.DOCUMENT, UKOType.FUNCTION, UKOType.CLASS,
        UKOType.TABLE, UKOType.COLUMN, UKOType.MESSAGE, UKOType.TICKET,
    },
    "changed": set(UKOType),
    "modified": {UKOType.FILE, UKOType.DOCUMENT},
    "same_as": {UKOType.PERSON, UKOType.NAME},
    "authored_by": {UKOType.PERSON, UKOType.NAME},
    "assigned_to": {UKOType.PERSON, UKOType.NAME},
    "part_of_workspace": {UKOType.WORKSPACE},
}


def validate_relationship(
    relationship: str,
    target_type: UKOType,
) -> tuple[bool, str]:
    """Returns (is_valid, reason). Reason is empty string when valid."""
    valid_targets = VALID_RELATIONSHIP_TARGETS.get(relationship)
    if valid_targets is None:
        return False, f"Unknown relationship type: {relationship}"
    if target_type not in valid_targets:
        allowed = ", ".join(sorted(t.value for t in valid_targets))
        return False, (
            f"Relationship '{relationship}' cannot target '{target_type.value}'. "
            f"Allowed targets: {allowed}"
        )
    return True, ""
