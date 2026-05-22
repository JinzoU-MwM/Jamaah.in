package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"go.uber.org/zap"

	"github.com/jamaah-in/v2/internal/auth/handler"
	"github.com/jamaah-in/v2/internal/auth/repository"
	"github.com/jamaah-in/v2/internal/auth/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	sharedConfig "github.com/jamaah-in/v2/internal/shared/config"
	sharedDB "github.com/jamaah-in/v2/internal/shared/database"
	sharedLogger "github.com/jamaah-in/v2/internal/shared/logger"
	sharedRedis "github.com/jamaah-in/v2/internal/shared/redis"
)

func main() {
	cfg := sharedConfig.Load()
	cfg.Database.DBName = "jamaah_auth"
	cfg.Server.Port = 50051
	if p := os.Getenv("AUTH_SERVICE_PORT"); p != "" {
		fmt.Sscan(p, &cfg.Server.Port)
	}

	logger := sharedLogger.New(cfg.App.Env)
	logger.Infof("starting auth service on :%d", cfg.Server.Port)

	ctx := context.Background()

	pool, err := sharedDB.Connect(ctx, cfg.Database.DSN())
	if err != nil {
		logger.Fatalf("connect to database: %v", err)
	}
	defer sharedDB.Close(pool)
	logger.Info("connected to database")

	rdb, err := sharedRedis.New(cfg.Redis.Addr, cfg.Redis.Password, cfg.Redis.DB)
	if err != nil {
		logger.Fatalf("connect to redis: %v", err)
	}
	defer rdb.Close()
	logger.Info("connected to redis")

	accessTTL := sharedAuth.ParseDuration(cfg.JWT.AccessTTL)
	refreshTTL := sharedAuth.ParseDuration(cfg.JWT.RefreshTTL)

	var jwtManager *sharedAuth.JWTManager
	if _, err := os.Stat(cfg.JWT.PrivateKeyPath); err == nil {
		jwtManager, err = sharedAuth.NewJWTManager(cfg.JWT.PrivateKeyPath, cfg.JWT.PublicKeyPath, accessTTL, refreshTTL)
		if err != nil {
			logger.Fatalf("init jwt manager: %v", err)
		}
		logger.Info("JWT manager initialized with RSA keys")
	} else {
		logger.Warn("JWT keys not found, running without JWT validation")
		jwtManager = nil
	}

	authRepo := repository.NewAuthRepo(pool)
	authRepo.StartCleanupScheduler(ctx)
	authService := service.NewAuthService(authRepo, jwtManager, rdb)
	authHandler := handler.NewAuthHandler(authService)

	app := fiber.New(fiber.Config{
		AppName:      "jamaah-auth-service",
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	})

	app.Use(recover.New())

	authPublic := app.Group("/api/v1/auth")
	authPublic.Post("/register", authHandler.Register)
	authPublic.Post("/login", authHandler.Login)
	authPublic.Post("/refresh", authHandler.RefreshToken)

	authPrivate := app.Group("/api/v1/auth", authMiddleware(jwtManager, logger))
	authPrivate.Post("/logout", authHandler.Logout)
	authPrivate.Get("/me", authHandler.GetMe)
	authPrivate.Put("/me", authHandler.UpdateMe)

	orgs := app.Group("/api/v1/orgs", authMiddleware(jwtManager, logger))
	orgs.Post("/", authHandler.CreateOrganization)
	orgs.Get("/", authHandler.GetOrganization)
	orgs.Get("/members", authHandler.ListTeamMembers)
	orgs.Get("/users", authHandler.ListUsersByOrg)
	orgs.Post("/members", authHandler.AddTeamMember)
	orgs.Delete("/members/:userId", authHandler.RemoveTeamMember)
	orgs.Put("/members/:userId/role", authHandler.UpdateMemberRole)
	orgs.Post("/invite", authHandler.InviteMember)

	app.Post("/api/v1/invite/accept", authMiddleware(jwtManager, logger), authHandler.AcceptInvite)

	go func() {
		if err := app.Listen(fmt.Sprintf(":%d", cfg.Server.Port)); err != nil {
			logger.Fatalf("fiber listen: %v", err)
		}
	}()
	logger.Infof("auth service listening on :%d", cfg.Server.Port)

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("shutting down auth service...")
	shutdownCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()
	if err := app.ShutdownWithContext(shutdownCtx); err != nil {
		logger.Errorf("fiber shutdown: %v", err)
	}
}

func authMiddleware(jwtMgr *sharedAuth.JWTManager, logger *zap.SugaredLogger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		authHeader := c.Get("Authorization")
		if authHeader == "" {
			return c.Status(401).JSON(fiber.Map{"success": false, "error": "missing authorization header"})
		}

		tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
		if tokenStr == authHeader {
			return c.Status(401).JSON(fiber.Map{"success": false, "error": "invalid authorization format"})
		}

		if jwtMgr == nil {
			return c.Status(500).JSON(fiber.Map{"success": false, "error": "JWT not configured"})
		}

		claims, err := jwtMgr.ValidateToken(tokenStr)
		if err != nil {
			return c.Status(401).JSON(fiber.Map{"success": false, "error": "invalid or expired token"})
		}

		c.Locals("claims", claims)
		return c.Next()
	}
}