"""
Unit tests for validator functions.
"""
import pytest
from app.services.validators import (
    validate_nik,
    validate_passport_number,
    validate_date,
    validate_kewarganegaraan,
    validate_visa_number,
)


class TestValidateNIK:
    """Test NIK validation."""
    
    def test_valid_nik(self):
        """16-digit NIK should pass (returns None)."""
        assert validate_nik("1234567890123456") is None
    
    def test_nik_too_short(self):
        """15-digit NIK should fail."""
        error = validate_nik("123456789012345")
        assert error is not None
        assert "16 digit" in error.lower()
    
    def test_nik_too_long(self):
        """17-digit NIK should fail."""
        error = validate_nik("12345678901234567")
        assert error is not None
    
    def test_nik_with_letters(self):
        """NIK with letters should be cleaned and validated."""
        # Letters are removed, so this fails (less than 16 digits after cleaning)
        error = validate_nik("123456789012345a")
        assert error is not None
    
    def test_empty_nik(self):
        """Empty NIK should pass (returns None, field is optional)."""
        assert validate_nik("") is None
        assert validate_nik(None) is None


class TestValidatePassportNumber:
    """Test passport number validation."""
    
    def test_valid_passport(self):
        """Valid passport (letter + 6-7 digits) should pass."""
        assert validate_passport_number("A1234567") is None
        assert validate_passport_number("B123456") is None
    
    def test_passport_only_digits(self):
        """Passport without letter should fail."""
        error = validate_passport_number("1234567")
        assert error is not None
        assert "tidak valid" in error.lower()
    
    def test_passport_too_short(self):
        """Too short passport should fail."""
        error = validate_passport_number("A12345")
        assert error is not None
    
    def test_empty_passport(self):
        """Empty passport should pass (optional field)."""
        assert validate_passport_number("") is None
        assert validate_passport_number(None) is None


class TestValidateDate:
    """Test date validation."""
    
    def test_valid_date_dd_mm_yyyy(self):
        """DD-MM-YYYY format should pass."""
        assert validate_date("15-03-1990", "Tanggal Lahir") is None
    
    def test_valid_date_yyyy_mm_dd(self):
        """YYYY-MM-DD format should pass."""
        assert validate_date("1990-03-15", "Tanggal Lahir") is None
    
    def test_valid_date_with_slashes(self):
        """DD/MM/YYYY format should pass."""
        assert validate_date("15/03/1990", "Tanggal Lahir") is None
    
    def test_invalid_date(self):
        """Invalid date (32nd of month) should fail."""
        error = validate_date("32-03-1990", "Tanggal Lahir")
        assert error is not None
        assert "tidak valid" in error.lower()
    
    def test_invalid_format(self):
        """Invalid format should fail."""
        error = validate_date("March 15 1990", "Tanggal Lahir")
        assert error is not None
    
    def test_empty_date(self):
        """Empty date should pass (optional field)."""
        assert validate_date("", "Tanggal Lahir") is None
        assert validate_date(None, "Tanggal Lahir") is None


class TestValidateKewarganegaraan:
    """Test citizenship validation."""
    
    def test_valid_wni(self):
        """WNI should pass."""
        assert validate_kewarganegaraan("WNI") is None
        assert validate_kewarganegaraan("wni") is None
    
    def test_valid_wna(self):
        """WNA should pass."""
        assert validate_kewarganegaraan("WNA") is None
        assert validate_kewarganegaraan("wna") is None
    
    def test_invalid_citizenship(self):
        """Invalid citizenship should fail."""
        error = validate_kewarganegaraan("MALAYSIA")
        assert error is not None
        assert "wni atau wna" in error.lower()
    
    def test_empty_citizenship(self):
        """Empty citizenship should pass (optional field)."""
        assert validate_kewarganegaraan("") is None
        assert validate_kewarganegaraan(None) is None


class TestValidateVisaNumber:
    """Test visa number validation."""
    
    def test_valid_visa(self):
        """Valid visa (8+ chars) should pass."""
        assert validate_visa_number("ABC12345") is None
        assert validate_visa_number("1234567890") is None
    
    def test_visa_too_short(self):
        """Too short visa should fail."""
        error = validate_visa_number("1234567")
        assert error is not None
        assert "terlalu pendek" in error.lower()
    
    def test_empty_visa(self):
        """Empty visa should pass (optional field)."""
        assert validate_visa_number("") is None
        assert validate_visa_number(None) is None
