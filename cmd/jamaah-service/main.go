package main

import (
	"context"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"go.uber.org/zap"

	"github.com/jamaah-in/v2/internal/jamaah/handler"
	"github.com/jamaah-in/v2/internal/jamaah/repository"
	"github.com/jamaah-in/v2/internal/jamaah/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	sharedConfig "github.com/jamaah-in/v2/internal/shared/config"
	sharedDB "github.com/jamaah-in/v2/internal/shared/database"
	sharedLogger "github.com/jamaah-in/v2/internal/shared/logger"
)

func main() {
	cfg := sharedConfig.Load()
	cfg.Database.DBName = "jamaah_crm"
	cfg.Server.Port = 50053
	if p := os.Getenv("JAMAAH_SERVICE_PORT"); p != "" {
		cfg.Server.Port, _ = strconv.Atoi(p)
	}

	logger := sharedLogger.New(cfg.App.Env)
	logger.Infof("starting jamaah service on :%d", cfg.Server.Port)

	ctx := context.Background()
	pool, err := sharedDB.Connect(ctx, cfg.Database.DSN())
	if err != nil {
		logger.Fatalf("connect to database: %v", err)
	}
	defer sharedDB.Close(pool)
	logger.Info("connected to database")

	var jwtManager *sharedAuth.JWTManager
	if _, err := os.Stat(cfg.JWT.PrivateKeyPath); err == nil {
		accessTTL := sharedAuth.ParseDuration(cfg.JWT.AccessTTL)
		refreshTTL := sharedAuth.ParseDuration(cfg.JWT.RefreshTTL)
		jwtManager, err = sharedAuth.NewJWTManager(cfg.JWT.PrivateKeyPath, cfg.JWT.PublicKeyPath, accessTTL, refreshTTL)
		if err != nil {
			logger.Fatalf("init jwt manager: %v", err)
		}
		logger.Info("JWT manager initialized")
	} else {
		logger.Warn("JWT keys not found - running without auth")
	}

	jamaahRepo := repository.NewJamaahRepo(pool)
	jamaahService := service.NewJamaahService(jamaahRepo)
	jamaahHandler := handler.NewJamaahHandler(jamaahService)

	app := fiber.New(fiber.Config{
		AppName:      "jamaah-crm-service",
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	})
	app.Use(recover.New())

	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{"status": "ok", "service": "jamaah-crm"})
	})

	authMW := authMiddleware(jwtManager, logger)

	jamaah := app.Group("/api/v1/jamaah", authMW)
	jamaah.Post("/", jamaahHandler.CreateProfile)
	jamaah.Get("/", jamaahHandler.ListProfiles)
	jamaah.Get("/search/nik/:nik", jamaahHandler.FindByNIK)
	jamaah.Get("/search/paspor/:paspor", jamaahHandler.FindByPaspor)
	jamaah.Get("/dashboard/alerts", jamaahHandler.DashboardAlerts)
	jamaah.Get("/:id", jamaahHandler.GetProfile)
	jamaah.Put("/:id", jamaahHandler.UpdateProfile)
	jamaah.Delete("/:id", jamaahHandler.DeleteProfile)

	jamaah.Post("/:id/register", jamaahHandler.RegisterToPackage)
	jamaah.Get("/:id/registrations/:pkgId", jamaahHandler.GetRegistration)
	jamaah.Patch("/:id/registrations/:pkgId/status", jamaahHandler.UpdatePipelineStatus)
	jamaah.Delete("/:id/registrations/:pkgId", jamaahHandler.RemoveFromPackage)

	jamaah.Post("/:id/notes", jamaahHandler.AddNote)
	jamaah.Get("/:id/notes", jamaahHandler.ListNotes)

	jamaah.Post("/:id/follow-ups", jamaahHandler.AddFollowUp)
	jamaah.Get("/follow-ups", jamaahHandler.ListFollowUps)
	jamaah.Patch("/follow-ups/:followUpId/complete", jamaahHandler.CompleteFollowUp)

	jamaah.Post("/:id/documents", jamaahHandler.UploadDocument)
	jamaah.Get("/:id/documents", jamaahHandler.ListDocuments)
	jamaah.Patch("/:id/documents/:docId/status", jamaahHandler.UpdateDocumentStatus)

	jamaah.Get("/by-package/:pkgId", jamaahHandler.ListByPackage)

	go func() {
		if err := app.Listen(":" + strconv.Itoa(cfg.Server.Port)); err != nil {
			logger.Fatalf("jamaah service listen: %v", err)
		}
	}()
	logger.Infof("jamaah service listening on :%d", cfg.Server.Port)

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logger.Info("shutting down jamaah service...")
	app.Shutdown()
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