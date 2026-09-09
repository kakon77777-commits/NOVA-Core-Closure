
def _tags(codes):
    from nova_core.paradigm import paradigm_by_code
    return tuple(paradigm_by_code(code) for code in codes)


def test_monotone_fill_chain_is_legal():
    from nova_core.paradigm_planner import validate_bonds
    decision = validate_bonds(_tags(["DCD","DJD","DPD","DRD"]))
    assert decision.legal
    assert not decision.violations


def test_fill_complexity_cannot_increase_without_reset():
    from nova_core.paradigm_planner import validate_bonds
    decision = validate_bonds(_tags(["DPD","DJD"]))
    assert not decision.legal
    assert any(v.rule == "fill_monotonicity" for v in decision.violations)


def test_recognition_is_terminal_under_stable_conditions():
    from nova_core.paradigm_planner import validate_bonds
    decision = validate_bonds(_tags(["DRD","DPD"]))
    assert not decision.legal
    assert any(v.rule == "recognition_terminal" for v in decision.violations)


def test_explicit_stability_reset_starts_new_chain_segment():
    from nova_core.paradigm_planner import validate_bonds
    decision = validate_bonds(_tags(["DRD","DCD"]), stability_resets=(0,))
    assert decision.legal
    assert any(o.kind == "stability_reset" for o in decision.obligations)


def test_base_space_conversion_is_asymmetric_and_d_to_c_creates_obligation():
    from nova_core.paradigm_planner import validate_bonds
    cd = validate_bonds(_tags(["CCC","DCD"]))
    dc = validate_bonds(_tags(["DCD","CCC"]))
    assert cd.legal and dc.legal
    assert dc.conversion_cost > cd.conversion_cost
    assert any(o.kind == "reconstruction_assumption" for o in dc.obligations)
