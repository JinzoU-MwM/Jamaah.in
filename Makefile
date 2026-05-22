.PHONY: all build run test lint proto migrate

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
GOGET=$(GOCMD) get
GOMOD=$(GOCMD) mod

# Service binaries
GATEWAY=./cmd/api-gateway
AUTH=./cmd/auth-service
PACKAGE=./cmd/package-service
JAMAAH=./cmd/jamaah-service
INVOICE=./cmd/invoice-service
FINANCE=./cmd/finance-service
AIOCR=./cmd/ai-ocr-service
VENDOR=./cmd/vendor-service

# Output directory
BIN_DIR=./bin

# Docker
DOCKER_COMPOSE=docker compose -f deployments/docker-compose.yml

# Proto
PROTOC_GEN_GO=protoc-gen-go
PROTOC_GEN_GO_GRPC=protoc-gen-go-grpc

all: build

## Build all services
build:
	$(GOBUILD) -o $(BIN_DIR)/api-gateway $(GATEWAY)
	$(GOBUILD) -o $(BIN_DIR)/auth-service $(AUTH)
	$(GOBUILD) -o $(BIN_DIR)/package-service $(PACKAGE)
	$(GOBUILD) -o $(BIN_DIR)/jamaah-service $(JAMAAH)
	$(GOBUILD) -o $(BIN_DIR)/invoice-service $(INVOICE)
	$(GOBUILD) -o $(BIN_DIR)/finance-service $(FINANCE)
	$(GOBUILD) -o $(BIN_DIR)/ai-ocr-service $(AIOCR)
	$(GOBUILD) -o $(BIN_DIR)/vendor-service $(VENDOR)

## Build individual services
build-gateway:
	$(GOBUILD) -o $(BIN_DIR)/api-gateway $(GATEWAY)

build-auth:
	$(GOBUILD) -o $(BIN_DIR)/auth-service $(AUTH)

build-package:
	$(GOBUILD) -o $(BIN_DIR)/package-service $(PACKAGE)

build-jamaah:
	$(GOBUILD) -o $(BIN_DIR)/jamaah-service $(JAMAAH)

build-invoice:
	$(GOBUILD) -o $(BIN_DIR)/invoice-service $(INVOICE)

build-finance:
	$(GOBUILD) -o $(BIN_DIR)/finance-service $(FINANCE)

build-aiocr:
	$(GOBUILD) -o $(BIN_DIR)/ai-ocr-service $(AIOCR)

build-vendor:
	$(GOBUILD) -o $(BIN_DIR)/vendor-service $(VENDOR)

## Run services locally (development)
run-gateway:
	$(GOCMD) run $(GATEWAY)

run-auth:
	$(GOCMD) run $(AUTH)

run-package:
	$(GOCMD) run $(PACKAGE)

run-jamaah:
	$(GOCMD) run $(JAMAAH)

run-invoice:
	$(GOCMD) run $(INVOICE)

run-finance:
	$(GOCMD) run $(FINANCE)

run-aiocr:
	$(GOCMD) run $(AIOCR)

run-vendor:
	$(GOCMD) run $(VENDOR)

## Test
test:
	$(GOTEST) -v ./internal/...

test-auth:
	$(GOTEST) -v ./internal/auth/...

test-package:
	$(GOTEST) -v ./internal/package/...

test-jamaah:
	$(GOTEST) -v ./internal/jamaah/...

test-invoice:
	$(GOTEST) -v ./internal/invoice/...

test-finance:
	$(GOTEST) -v ./internal/finance/...

test-vendor:
	$(GOTEST) -v ./internal/vendor_svc/...

## Docker
docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-build:
	$(DOCKER_COMPOSE) build

docker-ps:
	$(DOCKER_COMPOSE) ps

docker-logs:
	$(DOCKER_COMPOSE) logs -f

## Database migrations
migrate-up-auth:
	$(GOCMD) run cmd/migration/main.go -service auth -direction up

migrate-up-package:
	$(GOCMD) run cmd/migration/main.go -service package -direction up

migrate-up-jamaah:
	$(GOCMD) run cmd/migration/main.go -service jamaah -direction up

migrate-up-invoice:
	$(GOCMD) run cmd/migration/main.go -service invoice -direction up

migrate-up-finance:
	$(GOCMD) run cmd/migration/main.go -service finance -direction up

migrate-up-aiocr:
	$(GOCMD) run cmd/migration/main.go -service aiocr -direction up

migrate-up-vendor:
	$(GOCMD) run cmd/migration/main.go -service vendor -direction up

migrate-up-all: migrate-up-auth migrate-up-package migrate-up-jamaah migrate-up-invoice migrate-up-finance migrate-up-aiocr migrate-up-vendor

## Proto generation
proto:
	./scripts/generate-proto.sh

## Tidy
tidy:
	$(GOMOD) tidy

## Clean
clean:
	$(GOCLEAN)
	rm -rf $(BIN_DIR)