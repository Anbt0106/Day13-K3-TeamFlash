from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_passport() -> None:
    out = scrub_text("Passport number: C1234567")
    assert "C1234567" not in out
    assert "REDACTED_PASSPORT" in out


def test_scrub_address_vn() -> None:
    out_accent = scrub_text("Địa chỉ: 123 đường Nguyễn Huệ, phường Bến Nghé, quận 1, thành phố Hồ Chí Minh")
    assert "REDACTED_ADDRESS_VN" in out_accent

    out_no_accent = scrub_text("Dia chi: 123 duong Nguyen Hue, phuong Ben Nghe, quan 1, thanh pho Ho Chi Minh")
    assert "REDACTED_ADDRESS_VN" in out_no_accent
