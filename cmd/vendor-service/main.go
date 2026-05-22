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

	"github.com/jamaah-in/v2/internal/vendor_svc/handler"
	"github.com/jamaah-in/v2/internal/vendor_svc/repository"
	"github.com/jamaah-in/v2/internal/vendor_svc/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	sharedConfig "github.com/jamaah-in/v2/internal/shared/config"
	sharedDB "github.com/jamaah-in/v2/internal/shared/database"
	sharedLogger "github.com/jamaah-in/v2/internal/shared/logger"
)

func main() {
	cfg := sharedConfig.Load()
	cfg.Database.DBName = "jamaah_vendor"
	cfg.Server.Port = 50057
	if p := os.Getenv("VENDOR_SERVICE_PORT"); p != "" {
		cfg.Server.Port, _ = strconv.Atoi(p)
	}

	logger := sharedLogger.New(cfg.App.Env)
	logger.Infof("starting vendor service on :%d", cfg.Server.Port)

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

	vendorRepo := repository.NewVendorRepo(pool)
	vendorService := service.NewVendorService(vendorRepo)
	vendorHandler := handler.NewVendorHandler(vendorService)

	app := fiber.New(fiber.Config{
		AppName:      "jamaah-vendor-service",
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	})
	app.Use(recover.New())

	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{"status": "ok", "service": "vendor"})
	})

	authMW := authMiddleware(jwtManager, logger)

	api := app.Group("/api/v1/vendors", authMW)

	// Vendor master CRUD (static routes before param routes)
	api.Post("/", vendorHandler.CreateVendor)
	api.Get("/", vendorHandler.ListVendors)

	// Vendor bills (static routes)
	api.Post("/bills", vendorHandler.CreateBill)
	api.Get("/bills", vendorHandler.ListBills)
	api.Get("/bills/overdue", vendorHandler.GetOverdueBills)
	api.Get("/bills/due-soon", vendorHandler.GetBillsDueSoon)
	api.Get("/bills/summary", vendorHandler.GetDebtSummary)

	// Vendor payments (static routes)
	api.Post("/bills/:billId/payments", vendorHandler.CreatePayment)
	api.Get("/bills/:billId/payments", vendorHandler.ListPaymentsByBill)
	api.Get("/payments/:id", vendorHandler.GetPayment)
	api.Delete("/payments/:id", vendorHandler.DeletePayment)

	// Param routes (must come after static routes)
	api.Get("/:id", vendorHandler.GetVendor)
	api.Put("/:id", vendorHandler.UpdateVendor)
	api.Delete("/:id", vendorHandler.DeleteVendor)
	api.Get("/bills/:id", vendorHandler.GetBill)
	api.Put("/bills/:id", vendorHandler.UpdateBill)
	api.Delete("/bills/:id", vendorHandler.DeleteBill)
	api.Get("/:vendorId/payments", vendorHandler.ListPaymentsByVendor)

	go func() {
		if err := app.Listen(":" + strconv.Itoa(cfg.Server.Port)); err != nil {
			logger.Fatalf("vendor service listen: %v", err)
		}
	}()
	logger.Infof("vendor service listening on :%d", cfg.Server.Port)

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logger.Info("shutting down vendor service...")
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