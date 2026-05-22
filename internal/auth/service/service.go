package service

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"

	"github.com/jamaah-in/v2/internal/auth/model"
	"github.com/jamaah-in/v2/internal/auth/repository"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	sharedRedis "github.com/jamaah-in/v2/internal/shared/redis"
)

type AuthService struct {
	repo     *repository.AuthRepo
	jwt      *sharedAuth.JWTManager
	redis    *sharedRedis.Client
}

func NewAuthService(repo *repository.AuthRepo, jwt *sharedAuth.JWTManager, redis *sharedRedis.Client) *AuthService {
	return &AuthService{
		repo:  repo,
		jwt:   jwt,
		redis: redis,
	}
}

func (s *AuthService) Register(ctx context.Context, req model.RegisterRequest) (*model.User, *model.Organization, *sharedAuth.TokenPair, error) {
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("hash password: %w", err)
	}

	userID := uuid.New()
	user := &model.User{
		ID:           userID,
		Email:        req.Email,
		Name:         req.Name,
		PasswordHash: string(hashedPassword),
		Role:         "owner",
		IsActive:     true,
	}
	if req.Phone != "" {
		normalizedPhone := req.Phone
		user.Phone = &normalizedPhone
	}

	if err := s.repo.CreateUser(ctx, user); err != nil {
		return nil, nil, nil, err
	}

	slug := repository.GenerateSlug(req.Name)
	slug, err = s.repo.GenerateUniqueSlug(ctx, slug)
	if err != nil {
		return nil, nil, nil, err
	}

	org := &model.Organization{
		ID:        uuid.New(),
		Name:      req.Name,
		Slug:      slug,
		CreatedBy: userID,
	}
	if err := s.repo.CreateOrganization(ctx, org); err != nil {
		return nil, nil, nil, err
	}

	member := &model.TeamMember{
		ID:     uuid.New(),
		OrgID:  org.ID,
		UserID: userID,
		Role:   "owner",
		Status: "active",
	}
	if err := s.repo.AddTeamMember(ctx, member); err != nil {
		return nil, nil, nil, err
	}

	tokens, err := s.jwt.GenerateTokenPair(userID, org.ID, "owner", user.Email)
	if err != nil {
		return nil, nil, nil, err
	}

	if err := s.storeRefreshToken(ctx, tokens.RefreshToken, userID); err != nil {
		return nil, nil, nil, err
	}

	s.repo.CreateAuditLog(ctx, &model.AuditLog{
		ID:     uuid.New(),
		OrgID:  &org.ID,
		UserID: &userID,
		Action: "user.register",
		Entity: "user",
		EntityID: &userID,
		NewValue: map[string]string{"email": user.Email, "name": user.Name},
	})

	return user, org, tokens, nil
}

func (s *AuthService) Login(ctx context.Context, req model.LoginRequest) (*model.User, *model.Organization, *sharedAuth.TokenPair, error) {
	user, err := s.repo.GetUserByEmail(ctx, req.Email)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("invalid credentials")
	}

	if !user.IsActive {
		return nil, nil, nil, fmt.Errorf("account is deactivated")
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		return nil, nil, nil, fmt.Errorf("invalid credentials")
	}

	org, member, err := s.getUserOrgAndRole(ctx, user.ID)
	if err != nil {
		return nil, nil, nil, err
	}

	role := "viewer"
	if member != nil {
		role = member.Role
	}

	tokens, err := s.jwt.GenerateTokenPair(user.ID, org.ID, role, user.Email)
	if err != nil {
		return nil, nil, nil, err
	}

	if err := s.storeRefreshToken(ctx, tokens.RefreshToken, user.ID); err != nil {
		return nil, nil, nil, err
	}

	return user, org, tokens, nil
}

func (s *AuthService) RefreshToken(ctx context.Context, refreshToken string) (*sharedAuth.TokenPair, error) {
	hash := hashToken(refreshToken)
	rt, err := s.repo.GetRefreshTokenByHash(ctx, hash)
	if err != nil {
		return nil, fmt.Errorf("invalid refresh token")
	}

	if rt.ExpiresAt.Before(time.Now()) {
		s.repo.DeleteRefreshToken(ctx, hash)
		return nil, fmt.Errorf("refresh token expired")
	}

	user, err := s.repo.GetUserByID(ctx, rt.UserID)
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}

	org, member, err := s.getUserOrgAndRole(ctx, user.ID)
	if err != nil {
		return nil, err
	}

	role := "viewer"
	if member != nil {
		role = member.Role
	}

	s.repo.DeleteRefreshToken(ctx, hash)

	tokens, err := s.jwt.GenerateTokenPair(user.ID, org.ID, role, user.Email)
	if err != nil {
		return nil, err
	}

	if err := s.storeRefreshToken(ctx, tokens.RefreshToken, user.ID); err != nil {
		return nil, err
	}

	return tokens, nil
}

func (s *AuthService) Logout(ctx context.Context, refreshToken string) error {
	if refreshToken == "" {
		return nil
	}
	hash := hashToken(refreshToken)
	return s.repo.DeleteRefreshToken(ctx, hash)
}

func (s *AuthService) GetUser(ctx context.Context, userID uuid.UUID) (*model.User, error) {
	return s.repo.GetUserByID(ctx, userID)
}

func (s *AuthService) UpdateUser(ctx context.Context, userID uuid.UUID, name, phone string) (*model.User, error) {
	user, err := s.repo.GetUserByID(ctx, userID)
	if err != nil {
		return nil, err
	}
	user.Name = name
	if phone != "" {
		user.Phone = &phone
	}
	if err := s.repo.UpdateUser(ctx, user); err != nil {
		return nil, err
	}
	return user, nil
}

func (s *AuthService) GetOrganization(ctx context.Context, orgID uuid.UUID) (*model.Organization, error) {
	return s.repo.GetOrganizationByID(ctx, orgID)
}

func (s *AuthService) CreateOrganization(ctx context.Context, userID uuid.UUID, req model.CreateOrgRequest) (*model.Organization, error) {
	slug := repository.GenerateSlug(req.Name)
	slug, err := s.repo.GenerateUniqueSlug(ctx, slug)
	if err != nil {
		return nil, err
	}

	org := &model.Organization{
		ID:          uuid.New(),
		Name:        req.Name,
		Slug:        slug,
		Address:     req.Address,
		Phone:       req.Phone,
		Email:       req.Email,
		BankName:    req.BankName,
		BankAccount: req.BankAccount,
		BankHolder:  req.BankHolder,
		CreatedBy:   userID,
	}
	if err := s.repo.CreateOrganization(ctx, org); err != nil {
		return nil, err
	}

	member := &model.TeamMember{
		ID:     uuid.New(),
		OrgID:  org.ID,
		UserID: userID,
		Role:   "owner",
		Status: "active",
	}
	s.repo.AddTeamMember(ctx, member)

	return org, nil
}

func (s *AuthService) AddTeamMember(ctx context.Context, orgID, userID, addedBy uuid.UUID, role string) (*model.TeamMember, error) {
	count, err := s.repo.CountTeamMembers(ctx, orgID)
	if err != nil {
		return nil, err
	}
	if count >= 50 {
		return nil, fmt.Errorf("team member limit reached (50)")
	}

	member := &model.TeamMember{
		ID:        uuid.New(),
		OrgID:     orgID,
		UserID:    userID,
		Role:      role,
		Status:    "active",
		InvitedBy: &addedBy,
	}
	if err := s.repo.AddTeamMember(ctx, member); err != nil {
		return nil, err
	}
	return member, nil
}

func (s *AuthService) RemoveTeamMember(ctx context.Context, orgID, userID uuid.UUID) error {
	member, err := s.repo.GetTeamMember(ctx, orgID, userID)
	if err != nil {
		return err
	}
	if member.Role == "owner" {
		return fmt.Errorf("cannot remove owner from organization")
	}
	return s.repo.RemoveTeamMember(ctx, orgID, userID)
}

func (s *AuthService) UpdateMemberRole(ctx context.Context, orgID, userID uuid.UUID, role string) error {
	member, err := s.repo.GetTeamMember(ctx, orgID, userID)
	if err != nil {
		return err
	}
	if member.Role == "owner" && role != "owner" {
		return fmt.Errorf("cannot change owner role; transfer ownership first")
	}
	return s.repo.UpdateMemberRole(ctx, orgID, userID, role)
}

func (s *AuthService) ListTeamMembers(ctx context.Context, orgID uuid.UUID) ([]model.TeamMember, error) {
	return s.repo.ListTeamMembers(ctx, orgID)
}

func (s *AuthService) ListUsersByOrg(ctx context.Context, orgID uuid.UUID) ([]model.User, error) {
	return s.repo.ListUsersByOrg(ctx, orgID)
}

func (s *AuthService) InviteMember(ctx context.Context, orgID, invitedBy uuid.UUID, email, role string) (*model.TeamInvite, error) {
	token := generateToken(32)
	invite := &model.TeamInvite{
		ID:        uuid.New(),
		OrgID:     orgID,
		Email:     email,
		Role:      role,
		Token:     token,
		InvitedBy: invitedBy,
		ExpiresAt: time.Now().Add(7 * 24 * time.Hour),
		Status:    "pending",
	}
	if err := s.repo.CreateTeamInvite(ctx, invite); err != nil {
		return nil, err
	}
	return invite, nil
}

func (s *AuthService) AcceptInvite(ctx context.Context, token string, userID uuid.UUID) (*model.TeamMember, error) {
	invite, err := s.repo.GetTeamInviteByToken(ctx, token)
	if err != nil {
		return nil, fmt.Errorf("invite not found")
	}
	if invite.Status != "pending" {
		return nil, fmt.Errorf("invite is no longer valid")
	}
	if time.Now().After(invite.ExpiresAt) {
		s.repo.UpdateInviteStatus(ctx, token, "expired")
		return nil, fmt.Errorf("invite has expired")
	}

	member := &model.TeamMember{
		ID:     uuid.New(),
		OrgID:  invite.OrgID,
		UserID: userID,
		Role:   invite.Role,
		Status: "active",
	}
	if err := s.repo.AddTeamMember(ctx, member); err != nil {
		return nil, err
	}

	s.repo.UpdateInviteStatus(ctx, token, "accepted")
	return member, nil
}

func (s *AuthService) ValidateToken(ctx context.Context, tokenStr string) (*sharedAuth.Claims, error) {
	claims, err := s.jwt.ValidateToken(tokenStr)
	if err != nil {
		return nil, err
	}

	tokenID := claims.ID
	blacklisted, err := s.redis.IsTokenBlacklisted(ctx, tokenID)
	if err != nil {
		return nil, err
	}
	if blacklisted {
		return nil, fmt.Errorf("token has been revoked")
	}

	return claims, nil
}

func (s *AuthService) getUserOrgAndRole(ctx context.Context, userID uuid.UUID) (*model.Organization, *model.TeamMember, error) {
	org, err := s.repo.GetOrgByUserID(ctx, userID)
	if err != nil {
		return nil, nil, err
	}
	member, err := s.repo.GetTeamMember(ctx, org.ID, userID)
	if err != nil {
		return org, nil, nil
	}
	return org, member, nil
}

func (s *AuthService) storeRefreshToken(ctx context.Context, refreshToken string, userID uuid.UUID) error {
	hash := hashToken(refreshToken)
	rt := &model.RefreshToken{
		ID:         uuid.New(),
		UserID:     userID,
		TokenHash:  hash,
		ExpiresAt:  time.Now().Add(7 * 24 * time.Hour),
	}
	return s.repo.CreateRefreshToken(ctx, rt)
}

func hashToken(token string) string {
	h := sha256.Sum256([]byte(token))
	return hex.EncodeToString(h[:])
}

func generateToken(length int) string {
	b := make([]byte, length)
	rand.Read(b)
	return hex.EncodeToString(b)[:length]
}