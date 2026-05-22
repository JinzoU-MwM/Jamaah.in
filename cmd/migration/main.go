package main

/*
Migration tool for all jamaah-in v2 services.
Usage:
  go run cmd/migration/main.go -service auth -direction up
  go run cmd/migration/main.go -service all -direction up
*/

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"
)

var services = []string{"auth", "package", "jamaah", "invoice", "finance", "aiocr", "vendor"}

func main() {
	service := flag.String("service", "all", "service name (auth, package, jamaah, invoice, finance, aiocr, vendor, all)")
	direction := flag.String("direction", "up", "migration direction (up, down)")
	dbHost := flag.String("host", "localhost", "postgres host")
	dbPort := flag.Int("port", 5433, "postgres port")
	dbUser := flag.String("user", "jamaah", "postgres user")
	dbPass := flag.String("password", "Jamaah123!", "postgres password")
	migrationsDir := flag.String("migrations", "./migrations", "path to migrations directory")
	flag.Parse()

	servicesToMigrate := []string{}
	if *service == "all" {
		servicesToMigrate = services
	} else {
		found := false
		for _, s := range services {
			if s == *service {
				found = true
				break
			}
		}
		if !found {
			log.Fatalf("unknown service: %s (valid: auth, package, jamaah, invoice, finance, aiocr, vendor, all)", *service)
		}
		servicesToMigrate = []string{*service}
	}

	for _, svc := range servicesToMigrate {
		dbName := getDBName(svc)
		dsn := fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=disable",
			*dbUser, *dbPass, *dbHost, *dbPort, dbName)

		migrationsPath := filepath.Join(*migrationsDir, svc)
		if _, err := os.Stat(migrationsPath); os.IsNotExist(err) {
			log.Printf("no migrations found for %s at %s, skipping", svc, migrationsPath)
			continue
		}

		absPath, _ := filepath.Abs(migrationsPath)
		fileURL := fmt.Sprintf("file:///%s", filepath.ToSlash(absPath))
		m, err := migrate.New(fileURL, dsn)
		if err != nil {
			log.Printf("ERROR: create migrate instance for %s: %v", svc, err)
			continue
		}

		switch *direction {
		case "up":
			if err := m.Up(); err != nil && err != migrate.ErrNoChange {
				log.Printf("ERROR: migrate %s up: %v", svc, err)
			} else {
				log.Printf("OK: %s migrations applied", svc)
			}
		case "down":
			if err := m.Steps(-1); err != nil && err != migrate.ErrNoChange {
				log.Printf("ERROR: migrate %s down: %v", svc, err)
			} else {
				log.Printf("OK: %s migration rolled back", svc)
			}
		default:
			log.Fatalf("unknown direction: %s (use up or down)", *direction)
		}

		m.Close()
	}
}

func getDBName(service string) string {
	switch service {
	case "jamaah":
		return "jamaah_crm"
	case "aiocr":
		return "jamaah_aiocr"
	case "vendor":
		return "jamaah_vendor"
	default:
		return fmt.Sprintf("jamaah_%s", service)
	}
}