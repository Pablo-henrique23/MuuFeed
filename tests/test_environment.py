def test_pyarrow_compativel_com_numpy():
    """Falha aqui = ambiente incompatível (nasem_dairy exige NumPy 1.x; use Python 3.12 e requirements.txt)."""
    import numpy, pyarrow  # noqa: F401
    assert numpy.__version__.split(".")[0] == "1", "nasem_dairy exige numpy<2"
