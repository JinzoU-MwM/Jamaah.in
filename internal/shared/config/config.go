package config

import (
	"fmt"
	"os"
	"strconv"
)

type Config struct {
	App        AppConfig
	Database   DatabaseConfig
	Redis      RedisConfig
	NATS       NATSConfig
	MinIO      MinIOConfig
	JWT        JWTConfig
	Server     ServerConfig
	Gemini     GeminiConfig
}

type AppConfig struct {
	Env string
}

type ServerConfig struct {
	Port int
}

type DatabaseConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	DBName   string
	SSLMode  string
}

func (d DatabaseConfig) DSN() string {
	return fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=%s",
		d.User, d.Password, d.Host, d.Port, d.DBName, d.SSLMode)
}

type RedisConfig struct {
	Addr     string
	Password string
	DB       int
}

type NATSConfig struct {
	Addr string
}

type MinIOConfig struct {
	Endpoint  string
	AccessKey string
	SecretKey string
	Bucket    string
	UseSSL    bool
}

type JWTConfig struct {
	PrivateKeyPath string
	PublicKeyPath  string
	AccessTTL      string
	RefreshTTL     string
}

type GeminiConfig struct {
	APIKey string
}

func Load() *Config {
	return &Config{
		App: AppConfig{
			Env: envOr("APP_ENV", "development"),
		},
		Server: ServerConfig{
			Port: intEnvOr("SERVER_PORT", 8080),
		},
		Database: DatabaseConfig{
			Host:     envOr("POSTGRES_HOST", "localhost"),
			Port:     intEnvOr("POSTGRES_PORT", 5433),
			User:     envOr("POSTGRES_USER", "jamaah"),
			Password: envOr("POSTGRES_PASSWORD", "Jamaah123!"),
			DBName:   envOr("POSTGRES_DB", "jamaah_auth"),
			SSLMode:  envOr("POSTGRES_SSLMODE", "disable"),
		},
		Redis: RedisConfig{
			Addr:     envOr("REDIS_ADDR", "localhost:6379"),
			Password: envOr("REDIS_PASSWORD", ""),
			DB:       intEnvOr("REDIS_DB", 0),
		},
		NATS: NATSConfig{
			Addr: envOr("NATS_ADDR", "nats://localhost:4222"),
		},
		MinIO: MinIOConfig{
			Endpoint:  envOr("MINIO_ENDPOINT", "localhost:9000"),
			AccessKey: envOr("MINIO_ACCESS_KEY", "minioadmin"),
			SecretKey: envOr("MINIO_SECRET_KEY", "minioadmin"),
			Bucket:    envOr("MINIO_BUCKET", "jamaah-docs"),
			UseSSL:    envOr("MINIO_USE_SSL", "false") == "true",
		},
		JWT: JWTConfig{
			PrivateKeyPath: envOr("JWT_PRIVATE_KEY_PATH", "./certs/private.pem"),
			PublicKeyPath:  envOr("JWT_PUBLIC_KEY_PATH", "./certs/public.pem"),
			AccessTTL:      envOr("JWT_ACCESS_TTL", "15m"),
			RefreshTTL:     envOr("JWT_REFRESH_TTL", "168h"),
		},
		Gemini: GeminiConfig{
			APIKey: envOr("GEMINI_API_KEY", ""),
		},
	}
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func intEnvOr(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	return fallback
}