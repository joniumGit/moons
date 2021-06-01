def test_tex():
    from vicarui.support.tex import sci_4
    assert "^{+1}" in sci_4(10.12)
    assert "^{+0}" in sci_4(1.1)
    assert "^{-1}" in sci_4(0.11)
