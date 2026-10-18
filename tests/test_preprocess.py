from detection.preprocess import clean


def test_leetspeak_is_undone():
    text, _, tricks = clean("0rion B@nk: Y0ur acc0unt is susp3nded")
    assert text.lower().startswith("orion bank: your account is suspended")
    assert "leetspeak" in tricks


def test_numbers_and_otps_are_not_changed():
    text, _, tricks = clean("Your OTP is 483920. A/C xxxx4471. Valid 24hrs. Call 0771234567")
    assert "483920" in text and "xxxx4471" in text and "24hrs" in text and "0771234567" in text
    assert tricks == []


def test_homoglyphs_and_zero_width():
    text, _, tricks = clean("Оrіоn Bаnk: blo​cked")
    assert text == "Orion Bank: blocked"
    assert {"homoglyph", "zero_width"} <= set(tricks)


def test_spaced_letters():
    text, _, _ = clean("C a l l  0 7 7 1 2 3 4 5 6 7  n o w")
    assert text == "Call 0771234567 now"


def test_sinhala_joiner_is_kept():
    # ZWJ inside a Sinhala word is real writing, not a trick.
    word = "ශ්‍රී"
    text, lang, tricks = clean(word + " ලංකා")
    assert "‍" in text and "zero_width" not in tricks and lang == "si"


def test_language_tags():
    assert clean("Your account is blocked. Call now.")[1] == "en"
    assert clean("Obage account eka block wenawa. Wahama call karanna.")[1] == "singlish"
    assert clean("ඔබගේ ගිණුම අවහිර වේ.")[1] == "si"
