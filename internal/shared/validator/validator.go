package validator

import (
	"regexp"
	"strconv"
	"strings"
)

var (
	nikRegex  = regexp.MustCompile(`^[0-9]{16}$`)
	emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	phoneRegex = regexp.MustCompile(`^(\+62|62|0)[0-9]{8,13}$`)
	uuidRegex  = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)
)

func IsValidNIK(nik string) bool {
	return nikRegex.MatchString(nik)
}

func IsValidEmail(email string) bool {
	return emailRegex.MatchString(email)
}

func IsValidPhone(phone string) bool {
	cleaned := strings.ReplaceAll(strings.ReplaceAll(phone, " ", ""), "-", "")
	return phoneRegex.MatchString(cleaned)
}

func IsValidUUID(id string) bool {
	return uuidRegex.MatchString(id)
}

func ParseUUID(s string) (string, error) {
	if !IsValidUUID(s) {
		return "", ErrInvalidUUID
	}
	return strings.ToLower(s), nil
}

func NormalizePhone(phone string) string {
	p := strings.TrimSpace(phone)
	p = strings.ReplaceAll(p, " ", "")
	p = strings.ReplaceAll(p, "-", "")
	if strings.HasPrefix(p, "+62") {
		p = "0" + p[3:]
	} else if strings.HasPrefix(p, "62") {
		p = "0" + p[2:]
	}
	return p
}

func ParseInt(s string, fallback int) int {
	v, err := strconv.Atoi(s)
	if err != nil {
		return fallback
	}
	return v
}

var (
	ErrInvalidUUID  = &ValidationError{Field: "id", Message: "invalid UUID format"}
	ErrInvalidEmail = &ValidationError{Field: "email", Message: "invalid email format"}
	ErrInvalidPhone = &ValidationError{Field: "phone", Message: "invalid phone number format"}
	ErrInvalidNIK   = &ValidationError{Field: "nik", Message: "NIK must be 16 digits"}
)

type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string {
	return e.Message
}