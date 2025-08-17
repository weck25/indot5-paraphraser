#!/bin/bash

# IndoT5 Paraphraser API Test Script
# Usage: ./scripts/test-api.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:5005"
TIMEOUT=30

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

test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-""}
    local description=$4
    
    log_info "Testing $description..."
    
    local curl_cmd="curl -s -w '\nHTTP Status: %{http_code}\nTime: %{time_total}s\n'"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl_cmd="$curl_cmd -X POST -H 'Content-Type: application/json' -d '$data'"
    fi
    
    curl_cmd="$curl_cmd --max-time $TIMEOUT $BASE_URL$endpoint"
    
    local response=$(eval $curl_cmd)
    local status_code=$(echo "$response" | grep "HTTP Status:" | cut -d' ' -f3)
    local time_taken=$(echo "$response" | grep "Time:" | cut -d' ' -f2)
    
    if [ "$status_code" = "200" ]; then
        log_success "$description - Status: $status_code, Time: ${time_taken}s"
        echo "$response" | head -n -2
    else
        log_error "$description - Status: $status_code"
        echo "$response" | head -n -2
        return 1
    fi
    
    echo ""
}

wait_for_service() {
    log_info "Waiting for service to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$BASE_URL/health" >/dev/null 2>&1; then
            log_success "Service is ready!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - Service not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Service failed to become ready after $max_attempts attempts"
    return 1
}

run_tests() {
    log_info "Starting API tests..."
    
    # Wait for service to be ready
    wait_for_service
    
    # Test 1: Health check
    test_endpoint "/health" "GET" "" "Health Check"
    
    # Test 2: Root endpoint
    test_endpoint "/" "GET" "" "Root Endpoint"
    
    # Test 3: Single paraphrase - friendly style
    test_endpoint "/paraphrase" "POST" '{"text": "Saya ingin membeli produk ini", "style": "friendly"}' "Single Paraphrase (Friendly)"
    
    # Test 4: Single paraphrase - formal style
    test_endpoint "/paraphrase" "POST" '{"text": "Terima kasih atas bantuannya", "style": "formal"}' "Single Paraphrase (Formal)"
    
    # Test 5: Single paraphrase - casual style
    test_endpoint "/paraphrase" "POST" '{"text": "Halo, bagaimana kabar Anda?", "style": "casual"}' "Single Paraphrase (Casual)"
    
    # Test 6: Single paraphrase - default style
    test_endpoint "/paraphrase" "POST" '{"text": "Produk ini sangat bagus", "style": "default"}' "Single Paraphrase (Default)"
    
    # Test 7: Batch paraphrase
    test_endpoint "/batch-paraphrase" "POST" '[{"text": "Saya ingin membeli produk ini", "style": "friendly"}, {"text": "Terima kasih atas bantuannya", "style": "formal"}]' "Batch Paraphrase"
    
    # Test 8: Error handling - invalid JSON
    log_info "Testing error handling - invalid JSON..."
    response=$(curl -s -w '\nHTTP Status: %{http_code}\n' -X POST -H 'Content-Type: application/json' -d '{"invalid": "json"' "$BASE_URL/paraphrase" 2>/dev/null || true)
    status_code=$(echo "$response" | grep "HTTP Status:" | cut -d' ' -f3)
    if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
        log_success "Error handling - Status: $status_code"
    else
        log_warning "Error handling - Status: $status_code (expected 422 or 400)"
    fi
    echo ""
    
    # Test 9: Error handling - empty text
    test_endpoint "/paraphrase" "POST" '{"text": "", "style": "friendly"}' "Error Handling (Empty Text)"
    
    log_success "All tests completed!"
}

show_help() {
    echo "IndoT5 Paraphraser API Test Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  test      Run all API tests"
    echo "  health    Test health endpoint only"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 test"
    echo "  $0 health"
}

# Main script
case "${1:-test}" in
    test)
        run_tests
        ;;
    health)
        test_endpoint "/health" "GET" "" "Health Check"
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
