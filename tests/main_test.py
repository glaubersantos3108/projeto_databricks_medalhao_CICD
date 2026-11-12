from projeto_completo_databricks_git.main import get_taxis, get_spark


def test_main():
    taxis = get_taxis(get_spark())
    assert taxis.count() > 5
