package model

import (
	"time"

	"github.com/google/uuid"
)

type Role string

const (
	RoleOwner   Role = "owner"
	RoleAdmin   Role = "admin"
	RoleFinance Role = "finance"
	RoleCS      Role = "cs"
	RoleViewer  Role = "viewer"
)

func (r Role) String() string { return string(r) }

func ValidRoles() []string {
	return []string{"owner", "admin", "finance", "cs", "viewer"}
}

type MemberStatus string

const (
	StatusActive  MemberStatus = "active"
	StatusPending MemberStatus = "pending"
	StatusRemoved MemberStatus = "removed"
)

type User struct {
	ID            uuid.UUID `json:"id" db:"id"`
	Email         string     `json:"email" db:"email"`
	Name          string     `json:"name" db:"name"`
	PasswordHash  string     `json:"-" db:"password_hash"`
	Phone         *string    `json:"phone,omitempty" db:"phone"`
	PhoneVerified bool       `json:"phone_verified" db:"phone_verified"`
	Role          string     `json:"role" db:"role"`
	IsActive      bool       `json:"is_active" db:"is_active"`
	CreatedAt     time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at" db:"updated_at"`
}

type Organization struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Name        string     `json:"name" db:"name"`
	Slug        string     `json:"slug" db:"slug"`
	LogoURL     *string    `json:"logo_url,omitempty" db:"logo_url"`
	Address     *string    `json:"address,omitempty" db:"address"`
	Phone       *string    `json:"phone,omitempty" db:"phone"`
	Email       *string    `json:"email,omitempty" db:"email"`
	BankName    *string    `json:"bank_name,omitempty" db:"bank_name"`
	BankAccount *string    `json:"bank_account,omitempty" db:"bank_account"`
	BankHolder  *string    `json:"bank_holder,omitempty" db:"bank_holder"`
	CreatedBy   uuid.UUID  `json:"created_by" db:"created_by"`
	CreatedAt   time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at" db:"updated_at"`
}

type TeamMember struct {
	ID        uuid.UUID  `json:"id" db:"id"`
	OrgID     uuid.UUID  `json:"org_id" db:"org_id"`
	UserID    uuid.UUID  `json:"user_id" db:"user_id"`
	Role      string     `json:"role" db:"role"`
	Status    string     `json:"status" db:"status"`
	InvitedBy *uuid.UUID `json:"invited_by,omitempty" db:"invited_by"`
	JoinedAt  time.Time  `json:"joined_at" db:"joined_at"`
}

type TeamInvite struct {
	ID        uuid.UUID `json:"id" db:"id"`
	OrgID     uuid.UUID `json:"org_id" db:"org_id"`
	Email     string    `json:"email" db:"email"`
	Role      string    `json:"role" db:"role"`
	Token     string    `json:"token" db:"token"`
	InvitedBy uuid.UUID `json:"invited_by" db:"invited_by"`
	ExpiresAt time.Time `json:"expires_at" db:"expires_at"`
	Status    string    `json:"status" db:"status"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

type RefreshToken struct {
	ID         uuid.UUID `json:"id" db:"id"`
	UserID     uuid.UUID `json:"user_id" db:"user_id"`
	TokenHash  string    `json:"-" db:"token_hash"`
	DeviceInfo *string   `json:"device_info,omitempty" db:"device_info"`
	ExpiresAt  time.Time `json:"expires_at" db:"expires_at"`
	CreatedAt  time.Time `json:"created_at" db:"created_at"`
}

type AuditLog struct {
	ID        uuid.UUID `json:"id" db:"id"`
	OrgID     *uuid.UUID `json:"org_id,omitempty" db:"org_id"`
	UserID    *uuid.UUID `json:"user_id,omitempty" db:"user_id"`
	Action    string     `json:"action" db:"action"`
	Entity    string     `json:"entity" db:"entity"`
	EntityID  *uuid.UUID `json:"entity_id,omitempty" db:"entity_id"`
	OldValue  any        `json:"old_value,omitempty" db:"old_value"`
	NewValue  any        `json:"new_value,omitempty" db:"new_value"`
	IPAddress string     `json:"ip_address" db:"ip_address"`
	CreatedAt time.Time  `json:"created_at" db:"created_at"`
}

type RegisterRequest struct {
	Name     string `json:"name" validate:"required,min=2,max=255"`
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=8,max=72"`
	Phone    string `json:"phone,omitempty" validate:"omitempty"`
}

type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required"`
}

type CreateOrgRequest struct {
	Name        string  `json:"name" validate:"required,min=2,max=255"`
	Address     *string `json:"address,omitempty"`
	Phone       *string `json:"phone,omitempty"`
	Email       *string `json:"email,omitempty"`
	BankName    *string `json:"bank_name,omitempty"`
	BankAccount *string `json:"bank_account,omitempty"`
	BankHolder  *string `json:"bank_holder,omitempty"`
}

type AddTeamMemberRequest struct {
	UserID uuid.UUID `json:"user_id" validate:"required"`
	Role   string    `json:"role" validate:"required,oneof=owner admin finance cs viewer"`
}

type InviteMemberRequest struct {
	Email string `json:"email" validate:"required,email"`
	Role  string `json:"role" validate:"required,oneof=owner admin finance cs viewer"`
}

type AcceptInviteRequest struct {
	Token string `json:"token" validate:"required"`
}

type LoginResponse struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    int64     `json:"expires_at"`
	User         User      `json:"user"`
	Organization *Organization `json:"organization,omitempty"`
}

type RefreshRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresAt    int64  `json:"expires_at"`
}