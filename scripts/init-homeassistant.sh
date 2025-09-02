#!/usr/bin/env bash
#
# Initialize Home Assistant with default user and location
# This script runs after Home Assistant starts to configure initial settings
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Wait for Home Assistant to be ready
wait_for_ha() {
    print_status "Waiting for Home Assistant to be ready..."
    local retries=60
    while [ $retries -gt 0 ]; do
        if curl -s -f http://localhost:8123 > /dev/null 2>&1; then
            break
        fi
        sleep 1
        retries=$((retries - 1))
    done
    
    if [ $retries -eq 0 ]; then
        print_warning "Home Assistant is not responding, but continuing setup"
        return 1
    fi
    
    print_success "Home Assistant is ready"
    return 0
}

# Create initial user via API (if onboarding is not completed)
create_initial_user() {
    print_status "Checking if initial setup is needed..."
    
    # Check if onboarding is complete
    local response=$(curl -s -X GET http://localhost:8123/api/onboarding 2>/dev/null || echo "error")
    
    if echo "$response" | grep -q '"done"'; then
        print_status "Home Assistant setup is already complete"
        return 0
    fi
    
    print_status "Creating initial user 'test' with password 'test'..."
    
    # Create user during onboarding
    local user_data='{
        "client_id": "http://localhost:8123/",
        "name": "Test User",
        "username": "test",
        "password": "test",
        "language": "en"
    }'
    
    local user_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$user_data" \
        http://localhost:8123/api/onboarding/users 2>/dev/null || echo "error")
    
    if echo "$user_response" | grep -q "auth_code"; then
        print_success "User created successfully"
        
        # Complete core config
        local core_data='{
            "location_name": "Tallinn",
            "latitude": 59.4370,
            "longitude": 24.7536,
            "elevation": 9,
            "unit_system": "metric",
            "time_zone": "Europe/Tallinn",
            "currency": "EUR"
        }'
        
        # Extract access token from user response
        local auth_code=$(echo "$user_response" | grep -o '"auth_code":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$auth_code" ]; then
            print_status "Configuring location and settings for Estonia..."
            
            curl -s -X POST \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $auth_code" \
                -d "$core_data" \
                http://localhost:8123/api/onboarding/core_config > /dev/null 2>&1
            
            # Complete analytics step
            curl -s -X POST \
                -H "Authorization: Bearer $auth_code" \
                -d '{}' \
                http://localhost:8123/api/onboarding/analytics > /dev/null 2>&1
            
            # Complete integration step
            curl -s -X POST \
                -H "Authorization: Bearer $auth_code" \
                -d '{}' \
                http://localhost:8123/api/onboarding/integration > /dev/null 2>&1
                
            print_success "Home Assistant configured for Estonia"
        fi
    else
        print_warning "Could not create user automatically"
    fi
}

# Main execution
main() {
    echo -e "\n${GREEN}🏠 Initializing Home Assistant for Development${NC}\n"
    
    if wait_for_ha; then
        create_initial_user
        print_success "Home Assistant initialization completed"
        echo -e "\n${GREEN}📋 Login Information:${NC}"
        echo -e "   • URL: ${YELLOW}http://localhost:8123${NC}"
        echo -e "   • Username: ${YELLOW}test${NC}"
        echo -e "   • Password: ${YELLOW}test${NC}"
        echo -e "   • Location: ${YELLOW}Tallinn, Estonia${NC}"
        echo ""
    else
        print_warning "Home Assistant is not ready for automatic setup"
        echo -e "\n${YELLOW}Manual setup may be required at http://localhost:8123${NC}"
    fi
}

# Run main function
main "$@"
