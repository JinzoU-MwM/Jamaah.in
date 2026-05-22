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

	"github.com/jamaah-in/v2/internal/finance/handler"
	"github.com/jamaah-in/v2/internal/finance/repository"
	"github.com/jamaah-in/v2/internal/finance/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	sharedConfig "github.com/jamaah-in/v2/internal/shared/config"
	sharedDB "github.com/jamaah-in/v2/internal/shared/database"
	sharedLogger "github.com/jamaah-in/v2/internal/shared/logger"
)

func main() {
	cfg := sharedConfig.Load()
	cfg.Database.DBName = "jamaah_finance"
	cfg.Server.Port = 50055
	if p := os.Getenv("FINANCE_SERVICE_PORT"); p != "" {
		cfg.Server.Port, _ = strconv.Atoi(p)
	}

	logger := sharedLogger.New(cfg.App.Env)
	logger.Infof("starting finance service on :%d", cfg.Server.Port)

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

	financeRepo := repository.NewFinanceRepo(pool)
	financeService := service.NewFinanceService(financeRepo)
	financeHandler := handler.NewFinanceHandler(financeService)

	app := fiber.New(fiber.Config{
		AppName:      "jamaah-finance-service",
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	})
	app.Use(recover.New())

	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{"status": "ok", "service": "finance"})
	})

	authMW := authMiddleware(jwtManager, logger)

	finance := app.Group("/api/v1/finance", authMW)
	expenses := finance.Group("/expenses")
	expenses.Post("/", financeHandler.CreateExpense)
	expenses.Get("/", financeHandler.ListExpenses)
	expenses.Get("/summary", financeHandler.GetSummary)
	expenses.Get("/overdue", financeHandler.GetOverdueExpenses)
	expenses.Get("/package/:pkgId", financeHandler.ListExpensesByPackage)
	expenses.Get("/:id", financeHandler.GetExpense)
	expenses.Put("/:id", financeHandler.UpdateExpense)
	expenses.Delete("/:id", financeHandler.DeleteExpense)

	go func() {
		if err := app.Listen(":" + strconv.Itoa(cfg.Server.Port)); err != nil {
			logger.Fatalf("finance service listen: %v", err)
		}
	}()
	logger.Infof("finance service listening on :%d", cfg.Server.Port)

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logger.Info("shutting down finance service...")
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