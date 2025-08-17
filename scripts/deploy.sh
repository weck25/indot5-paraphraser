#!/bin/bash

# IndoT5 Paraphraser Deployment Script
# Usage: ./scripts/deploy.sh [start|stop|restart|logs|status]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="indot5-paraphraser"
COMPOSE_FILE="docker-compose.yml"
PORT=5005

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
}

check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        log_warning "Port $PORT is already in use"
        return 1
    fi
    return 0
}

wait_for_health() {
    log_info "Waiting for service to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$PORT/health >/dev/null 2>&1; then
            log_success "Service is healthy!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - Service not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Service failed to become healthy after $max_attempts attempts"
    return 1
}

start_service() {
    log_info "Starting IndoT5 Paraphraser service..."
    
    check_docker
    check_port || log_warning "Port $PORT is in use, but continuing..."
    
    # Pull latest changes if git repository
    if [ -d ".git" ]; then
        log_info "Pulling latest changes..."
        git pull origin main || log_warning "Failed to pull latest changes"
    fi
    
    # Build and start service
    log_info "Building and starting service..."
    docker-compose -f $COMPOSE_FILE up -d --build
    
    # Wait for service to be healthy
    wait_for_health
    
    log_success "IndoT5 Paraphraser service started successfully!"
    log_info "Service URL: http://localhost:$PORT"
    log_info "Health check: http://localhost:$PORT/health"
    log_info "API docs: http://localhost:$PORT/docs"
}

stop_service() {
    log_info "Stopping IndoT5 Paraphraser service..."
    
    docker-compose -f $COMPOSE_FILE down
    
    log_success "IndoT5 Paraphraser service stopped!"
}

restart_service() {
    log_info "Restarting IndoT5 Paraphraser service..."
    
    stop_service
    sleep 2
    start_service
}

show_logs() {
    log_info "Showing logs for IndoT5 Paraphraser service..."
    docker-compose -f $COMPOSE_FILE logs -f
}

show_status() {
    log_info "Checking IndoT5 Paraphraser service status..."
    
    # Check if container is running
    if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        log_success "Service is running"
        
        # Show container status
        docker-compose -f $COMPOSE_FILE ps
        
        # Check health endpoint
        if curl -f http://localhost:$PORT/health >/dev/null 2>&1; then
            log_success "Health check passed"
            curl -s http://localhost:$PORT/health | jq . 2>/dev/null || curl -s http://localhost:$PORT/health
        else
            log_warning "Health check failed"
        fi
    else
        log_error "Service is not running"
        docker-compose -f $COMPOSE_FILE ps
    fi
}

update_service() {
    log_info "Updating IndoT5 Paraphraser service..."
    
    # Pull latest changes
    if [ -d ".git" ]; then
        git pull origin main
    fi
    
    # Rebuild and restart
    docker-compose -f $COMPOSE_FILE down
    docker-compose -f $COMPOSE_FILE build --no-cache
    docker-compose -f $COMPOSE_FILE up -d
    
    wait_for_health
    log_success "Service updated successfully!"
}

cleanup() {
    log_info "Cleaning up unused Docker resources..."
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    log_success "Cleanup completed!"
}

show_help() {
    echo "IndoT5 Paraphraser Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the service"
    echo "  stop      Stop the service"
    echo "  restart   Restart the service"
    echo "  logs      Show service logs"
    echo "  status    Show service status"
    echo "  update    Update and restart the service"
    echo "  cleanup   Clean up unused Docker resources"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# Main script
case "${1:-help}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    update)
        update_service
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
