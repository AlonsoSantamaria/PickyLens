from app.services.replay import CanonicalIntent, CanonicalRequirement, compatible


def intent():
    return CanonicalIntent(scenario_id="consultant", scenario_version=1,
        requirements=[CanonicalRequirement(key="cost"), CanonicalRequirement(key="questions")],
        accepted_clarifications={"priority": "cost"}, constraints={"budget": 8000},
        decisions={}, mapping_established=True)


def test_requirement_order_does_not_change_compatibility():
    a, b = intent(), intent()
    b.requirements.reverse()
    assert compatible(a, b)


def test_substantive_changes_block_replay():
    for field, value in [("constraints", {"budget": 9000}),
                         ("accepted_clarifications", {"priority": "speed"}),
                         ("decisions", {"option": "B"}), ("scenario_version", 2)]:
        a, b = intent(), intent()
        setattr(b, field, value)
        assert not compatible(a, b)


def test_unknown_mapping_or_duplicate_keys_block_replay():
    a, b = intent(), intent()
    b.mapping_established = False
    assert not compatible(a, b)
    b = intent()
    b.requirements.append(b.requirements[0])
    assert not compatible(a, b)


def test_constraint_types_are_material():
    a, b = intent(), intent()
    a.constraints = {"limit": 1}
    b.constraints = {"limit": True}
    assert not compatible(a, b)
