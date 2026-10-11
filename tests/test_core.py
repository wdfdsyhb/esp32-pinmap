import esp32_pinmap as ep


def test_three_boards_present():
    assert {"esp32", "esp32-s3", "esp32-c3"} <= set(ep.BOARDS)


def test_classic_strapping_pins_marked():
    b = ep.BOARDS["esp32"]
    for n in (0, 2, 5, 12, 15):
        assert b[n]["strapping"], f"GPIO{n} should be strapping on classic ESP32"


def test_classic_input_only_pins():
    b = ep.BOARDS["esp32"]
    for n in (34, 35, 36, 39):
        assert b[n]["input_only"]


def test_s3_flash_pins_blocked():
    b = ep.BOARDS["esp32-s3"]
    for n in range(26, 33):
        assert not ep.usable(b, n, for_output=True)


def test_s3_octal_psram_pins_blocked():
    b = ep.BOARDS["esp32-s3"]
    for n in range(33, 38):
        assert not ep.usable(b, n, for_output=True)


def test_c3_strapping_and_flash():
    b = ep.BOARDS["esp32-c3"]
    for n in (2, 8, 9):
        assert b[n]["strapping"]
    for n in range(11, 18):
        assert not ep.usable(b, n, for_output=True)


def test_usable_logic():
    b = ep.BOARDS["esp32-s3"]
    assert ep.usable(b, 4, for_output=True)
    assert not ep.usable(b, 0, for_output=True)   # strapping
    assert not ep.usable(b, 19, for_output=True)  # USB D-
    assert not ep.usable(b, 43, for_output=True)  # UART0 TX


def test_input_only_pin_usable_for_input_not_output():
    b = ep.BOARDS["esp32"]
    assert ep.usable(b, 34, for_output=False)
    assert not ep.usable(b, 34, for_output=True)


def test_missing_gpio_returns_false():
    b = ep.BOARDS["esp32-c3"]
    assert not ep.usable(b, 22, for_output=True)  # C3 无 GPIO22


def test_pin_info_mentions_reason():
    s = ep.pin_info(ep.BOARDS["esp32-s3"], 0)
    assert "strapping" in s.lower()


def test_safe_list_excludes_reserved():
    safe = ep.safe_pins(ep.BOARDS["esp32-c3"], for_output=True)
    assert 4 in safe
    assert 9 not in safe and 11 not in safe and 19 not in safe and 21 not in safe
