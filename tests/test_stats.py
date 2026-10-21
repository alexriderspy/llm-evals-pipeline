from evals.stats import cohen_kappa, paired_bootstrap


def test_identical_runs_have_an_interval_around_zero():
    a = [1, 0, 1, 1, 0, 1, 0, 1, 1, 1] * 3
    diff, low, high = paired_bootstrap(a, a)
    assert diff == 0 and low == 0 and high == 0


def test_a_clearly_better_run_excludes_zero():
    a = [0] * 20 + [1] * 10
    b = [1] * 28 + [0] * 2
    diff, low, high = paired_bootstrap(a, b)
    assert low > 0 and abs(diff - 0.6) < 1e-9


def test_kappa():
    assert cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert (
        abs(cohen_kappa([True, True, False, False], [True, False, True, False])) < 1e-9
    )
