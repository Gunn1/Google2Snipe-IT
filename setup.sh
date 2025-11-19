#!/bin/bash

################################################################################
# Google2Snipe-IT Setup Script
#
# This script automates the setup of Google2Snipe-IT for both development and
# production environments. It handles:
#   - Python venv creation and activation
#   - Dependency installation
#   - Environment configuration (.env file)
#   - Production SystemD timer setup
#   - Configuration validation
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
ENV_FILE="${SCRIPT_DIR}/.env"
SERVICE_FILE="/etc/systemd/system/google2snipeit.service"
TIMER_FILE="/etc/systemd/system/google2snipeit.timer"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

ask_yes_no() {
    local question="$1"
    local default="$2"  # "y" or "n"
    local response

    while true; do
        read -p "$(echo -e ${BLUE})$question (y/n)? ${NC}" -r response
        case "$response" in
            [yY]) return 0 ;;
            [nN]) return 1 ;;
            *)
                if [ "$default" = "y" ]; then
                    return 0
                elif [ "$default" = "n" ]; then
                    return 1
                fi
                ;;
        esac
    done
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    print_success "$1 found"
    return 0
}

################################################################################
# Validation Functions
################################################################################

check_prerequisites() {
    print_header "Checking Prerequisites"

    check_command "python3" || exit 1
    check_command "pip3" || exit 1

    local python_version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "Python version: $python_version"

    # Use Python itself to check version (most reliable)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python 3.8+ is required (you have $python_version)"
        exit 1
    fi
}

check_existing_setup() {
    print_header "Checking Existing Setup"

    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists at $VENV_DIR"
        if ! ask_yes_no "Do you want to recreate it"; then
            print_info "Skipping venv recreation"
            SKIP_VENV_SETUP=true
        else
            print_info "Removing existing venv..."
            rm -rf "$VENV_DIR"
        fi
    fi

    if [ -f "$ENV_FILE" ]; then
        print_warning "Configuration file already exists at $ENV_FILE"
        if ! ask_yes_no "Do you want to reconfigure it"; then
            print_info "Keeping existing configuration"
            SKIP_CONFIG_PROMPTS=true
            load_existing_env
            return
        fi
    fi
}

load_existing_env() {
    print_info "Loading existing configuration from $ENV_FILE..."

    # Source the .env file to load variables
    # Use grep and sed to extract values safely
    API_TOKEN=$(grep "^API_TOKEN=" "$ENV_FILE" | cut -d'=' -f2-)
    ENDPOINT_URL=$(grep "^ENDPOINT_URL=" "$ENV_FILE" | cut -d'=' -f2-)
    DEFAULT_MODEL_ID=$(grep "^SNIPE_IT_DEFAULT_MODEL_ID=" "$ENV_FILE" | cut -d'=' -f2-)
    MAC_FIELD=$(grep "^SNIPE_IT_FIELD_MAC_ADDRESS=" "$ENV_FILE" | cut -d'=' -f2-)
    SYNC_DATE_FIELD=$(grep "^SNIPE_IT_FIELD_SYNC_DATE=" "$ENV_FILE" | cut -d'=' -f2-)
    IP_FIELD=$(grep "^SNIPE_IT_FIELD_IP_ADDRESS=" "$ENV_FILE" | cut -d'=' -f2-)
    USER_FIELD=$(grep "^SNIPE_IT_FIELD_USER=" "$ENV_FILE" | cut -d'=' -f2-)
    FIELDSET_ID=$(grep "^SNIPE_IT_FIELDSET_ID=" "$ENV_FILE" | cut -d'=' -f2-)
    DELEGATED_ADMIN=$(grep "^DELEGATED_ADMIN=" "$ENV_FILE" | cut -d'=' -f2-)
    SERVICE_ACCOUNT_PATH=$(grep "^GOOGLE_SERVICE_ACCOUNT_FILE=" "$ENV_FILE" | cut -d'=' -f2-)
    PAGE_SIZE=$(grep "^GOOGLE_CHROMEOS_PAGE_SIZE=" "$ENV_FILE" | cut -d'=' -f2-)
    GEMINI_API_KEY=$(grep "^Gemini_APIKEY=" "$ENV_FILE" | cut -d'=' -f2-)
    ENVIRONMENT=$(grep "^ENVIRONMENT=" "$ENV_FILE" | cut -d'=' -f2-)

    print_success "Configuration loaded from existing .env file"
}

################################################################################
# Setup Functions
################################################################################

setup_venv() {
    print_header "Setting Up Python Virtual Environment"

    print_info "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"

    print_info "Activating virtual environment..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"

    print_info "Upgrading pip, setuptools, and wheel..."
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    print_success "Pip upgraded"
}

install_dependencies() {
    print_header "Installing Dependencies"

    print_info "Installing dependencies from requirements.txt..."
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip install -r "$SCRIPT_DIR/requirements.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

prompt_environment() {
    print_header "Environment Selection"

    echo "Select deployment environment:"
    echo "  1) Development (recommended for testing)"
    echo "  2) Production (requires SystemD setup)"

    while true; do
        read -p "Enter choice (1 or 2): " -r choice
        case "$choice" in
            1)
                ENVIRONMENT="development"
                print_success "Development environment selected"
                break
                ;;
            2)
                ENVIRONMENT="production"
                print_success "Production environment selected"
                break
                ;;
            *)
                print_error "Invalid choice"
                ;;
        esac
    done
}

prompt_snipeit_config() {
    print_header "Snipe-IT Configuration"

    read -p "Snipe-IT API Token: " -r API_TOKEN
    read -p "Snipe-IT API Endpoint URL (e.g., https://snipeit.example.com/api/v1): " -r ENDPOINT_URL
    read -p "Default Model ID (default: 87): " -r DEFAULT_MODEL_ID
    DEFAULT_MODEL_ID=${DEFAULT_MODEL_ID:-87}

    read -p "MAC Address Field ID (default: _snipeit_mac_address_1): " -r MAC_FIELD
    MAC_FIELD=${MAC_FIELD:-_snipeit_mac_address_1}

    read -p "Sync Date Field ID (default: _snipeit_sync_date_9): " -r SYNC_DATE_FIELD
    SYNC_DATE_FIELD=${SYNC_DATE_FIELD:-_snipeit_sync_date_9}

    read -p "IP Address Field ID (default: _snipeit_ip_address_3): " -r IP_FIELD
    IP_FIELD=${IP_FIELD:-_snipeit_ip_address_3}

    read -p "User Field ID (default: _snipeit_user_10): " -r USER_FIELD
    USER_FIELD=${USER_FIELD:-_snipeit_user_10}

    read -p "Fieldset ID (default: 9): " -r FIELDSET_ID
    FIELDSET_ID=${FIELDSET_ID:-9}
}

prompt_google_config() {
    print_header "Google Workspace Configuration"

    read -p "Google Delegated Admin Email: " -r DELEGATED_ADMIN
    read -p "Path to service_account.json (default: ./service_account.json): " -r SERVICE_ACCOUNT_PATH
    SERVICE_ACCOUNT_PATH=${SERVICE_ACCOUNT_PATH:-service_account.json}

    # Resolve relative path to absolute path
    if [[ "$SERVICE_ACCOUNT_PATH" != /* ]]; then
        SERVICE_ACCOUNT_PATH="$(cd "$(dirname "$SERVICE_ACCOUNT_PATH")" && pwd)/$(basename "$SERVICE_ACCOUNT_PATH")"
    fi

    # Check if service account file exists
    if [ ! -f "$SERVICE_ACCOUNT_PATH" ]; then
        print_warning "Service account file not found at: $SERVICE_ACCOUNT_PATH"
        print_info "Please ensure you place the service_account.json file in the project directory"
        if ! ask_yes_no "Continue anyway"; then
            exit 1
        fi
    else
        # Copy service account file to project directory if not already there
        if [ "$SERVICE_ACCOUNT_PATH" != "$SCRIPT_DIR/service_account.json" ]; then
            print_info "Copying service account file to project directory..."
            if ! cp "$SERVICE_ACCOUNT_PATH" "$SCRIPT_DIR/service_account.json" 2>/dev/null; then
                print_warning "Could not copy file (it may already be in the correct location)"
            else
                print_success "Service account file copied to project directory"
            fi
        else
            print_success "Service account file is already in the correct location"
        fi
    fi

    read -p "Google ChromeOS Page Size (default: 300): " -r PAGE_SIZE
    PAGE_SIZE=${PAGE_SIZE:-300}
}

prompt_gemini_config() {
    print_header "Google Gemini Configuration"

    read -p "Gemini API Key: " -r GEMINI_API_KEY
}

create_env_file() {
    print_header "Creating Configuration File"

    cat > "$ENV_FILE" << EOF
################################################################################
# Google2Snipe-IT Environment Configuration
# Generated by setup.sh on $(date)
# Environment: $ENVIRONMENT
################################################################################

# Snipe-IT Configuration
API_TOKEN=$API_TOKEN
ENDPOINT_URL=$ENDPOINT_URL
SNIPE_IT_DEFAULT_MODEL_ID=$DEFAULT_MODEL_ID
SNIPE_IT_FIELDSET_ID=$FIELDSET_ID
SNIPE_IT_FIELD_MAC_ADDRESS=$MAC_FIELD
SNIPE_IT_FIELD_SYNC_DATE=$SYNC_DATE_FIELD
SNIPE_IT_FIELD_IP_ADDRESS=$IP_FIELD
SNIPE_IT_FIELD_USER=$USER_FIELD

# Google Workspace Configuration
DELEGATED_ADMIN=$DELEGATED_ADMIN
GOOGLE_SERVICE_ACCOUNT_FILE=$SERVICE_ACCOUNT_PATH
GOOGLE_CHROMEOS_PAGE_SIZE=$PAGE_SIZE

# Gemini AI Configuration
Gemini_APIKEY=$GEMINI_API_KEY

# Application Configuration
ENVIRONMENT=$ENVIRONMENT
DEBUG=false
DRY_RUN=false

# Retry Configuration
MAX_RETRIES=4
RETRY_DELAY_SECONDS=20

# Logging Configuration
LOG_FILE=snipeit_errors.log
LOG_LEVEL=WARNING
EOF

    print_success "Environment file created at $ENV_FILE"
    print_warning "Keep this file secure - it contains API credentials"
}

create_systemd_files() {
    print_header "Creating SystemD Service and Timer Files"

    if [ "$ENVIRONMENT" != "production" ]; then
        print_info "Skipping SystemD setup for development environment"
        return
    fi

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_warning "Not running as root. SystemD files will be created but not installed."
        SYSTEMD_DIR="${SCRIPT_DIR}/systemd"
        mkdir -p "$SYSTEMD_DIR"
    else
        SYSTEMD_DIR="/etc/systemd/system"
    fi

    # Determine which user to run the service as
    # If running via sudo, use the original user; otherwise use current user
    local SERVICE_USER="${SUDO_USER:-$USER}"

    # Read the service template from the systemd directory
    if [ ! -f "$SCRIPT_DIR/systemd/google2snipeit.service.template" ]; then
        print_error "Service template not found at $SCRIPT_DIR/systemd/google2snipeit.service.template"
        return 1
    fi

    service_content=$(cat "$SCRIPT_DIR/systemd/google2snipeit.service.template")

    # Replace placeholders
    service_content="${service_content//%SERVICE_USER%/$SERVICE_USER}"
    service_content="${service_content//%WORKING_DIR%/$SCRIPT_DIR}"
    service_content="${service_content//%VENV_BIN%/$VENV_DIR/bin}"
    service_content="${service_content//%SCRIPT_DIR%/$SCRIPT_DIR}"

    echo "$service_content" > "${SYSTEMD_DIR}/google2snipeit.service"
    print_success "Service file created"

    # Read the timer template from the systemd directory
    if [ ! -f "$SCRIPT_DIR/systemd/google2snipeit.timer.template" ]; then
        print_error "Timer template not found at $SCRIPT_DIR/systemd/google2snipeit.timer.template"
        return 1
    fi

    timer_content=$(cat "$SCRIPT_DIR/systemd/google2snipeit.timer.template")

    echo "$timer_content" > "${SYSTEMD_DIR}/google2snipeit.timer"
    print_success "Timer file created"

    if [ "$EUID" -eq 0 ]; then
        print_info "Installing SystemD files..."
        systemctl daemon-reload
        print_success "SystemD files installed and reloaded"

        print_info "Verifying permissions..."
        # Ensure project directory is accessible
        chmod 755 "$SCRIPT_DIR"

        # Ensure .env and service_account.json are readable (but not world-readable for security)
        chmod 640 "$SCRIPT_DIR"/.env 2>/dev/null || true
        chmod 640 "$SCRIPT_DIR"/service_account.json 2>/dev/null || true

        print_success "Permissions configured for $SERVICE_USER"

        # Prompt to enable and start timer
        if ask_yes_no "Enable and start the timer now"; then
            systemctl enable google2snipeit.timer
            systemctl start google2snipeit.timer
            print_success "Timer enabled and started"
            print_info "Check timer status with: systemctl status google2snipeit.timer"
        fi
    else
        print_warning "Not running as root. SystemD files will be created but not fully configured."
        print_info "To complete installation, run these commands as root:"
        echo ""
        echo "  sudo install -m 644 ${SYSTEMD_DIR}/*.service /etc/systemd/system/"
        echo "  sudo install -m 644 ${SYSTEMD_DIR}/*.timer /etc/systemd/system/"
        echo "  sudo systemctl daemon-reload"
        echo "  sudo systemctl enable google2snipeit.timer"
        echo "  sudo systemctl start google2snipeit.timer"
        echo ""
    fi
}

validate_setup() {
    print_header "Validating Setup"

    local errors=0

    # Check venv
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found"
        ((errors++))
    else
        print_success "Virtual environment found"
    fi

    # Check .env file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found"
        ((errors++))
    else
        print_success "Environment file found"
        # Check for required keys
        if grep -q "API_TOKEN=" "$ENV_FILE"; then
            print_success "API_TOKEN configured"
        else
            print_warning "API_TOKEN not set in .env"
        fi
    fi

    # Check service account if provided
    if [ -f "$SCRIPT_DIR/service_account.json" ]; then
        print_success "Service account file found"
    else
        print_warning "Service account file not found - ensure it exists before running"
    fi

    if [ $errors -gt 0 ]; then
        print_error "Setup validation failed with $errors error(s)"
        return 1
    fi

    print_success "All validation checks passed"
    return 0
}

print_next_steps() {
    print_header "Setup Complete!"

    echo "Your Google2Snipe-IT installation is ready."
    echo ""
    echo "Next steps:"
    echo ""

    if [ "$ENVIRONMENT" = "production" ]; then
        echo "  1. Review the .env file at: $ENV_FILE"
        echo "  2. Ensure service_account.json is in the project directory"
        echo "  3. Check SystemD timer status:"
        echo "     systemctl status google2snipeit.timer"
        echo "  4. View recent sync logs:"
        echo "     journalctl -u google2snipeit.service -f"
        echo ""
        echo "  Timer Schedule:"
        echo "     - Runs daily at 2:00 AM"
        echo "     - Runs 1 minute after system boot"
        echo "     - Will catch up if system was offline"
        echo ""
        echo "  To manually trigger a sync:"
        echo "     systemctl start google2snipeit.service"
    else
        echo "  1. Review the .env file at: $ENV_FILE"
        echo "  2. Ensure service_account.json is in the project directory"
        echo "  3. Activate the virtual environment:"
        echo "     source $VENV_DIR/bin/activate"
        echo "  4. Test the sync (dry-run):"
        echo "     export DRY_RUN=true && python snipe-IT.py"
        echo "  5. Run the actual sync:"
        echo "     python snipe-IT.py"
        echo ""
        echo "  To deactivate the virtual environment:"
        echo "     deactivate"
    fi

    echo ""
    echo "  Documentation: See README.md for troubleshooting and advanced configuration"
    echo ""
}

################################################################################
# Main Setup Flow
################################################################################

main() {
    clear
    print_header "Welcome to Google2Snipe-IT Setup"
    echo "This script will guide you through configuring Google2Snipe-IT"
    echo "for either development or production use."
    echo ""

    # Run setup steps
    check_prerequisites
    check_existing_setup

    # Only setup venv if not skipped
    if [ "$SKIP_VENV_SETUP" != "true" ]; then
        setup_venv
        install_dependencies
    else
        print_info "Using existing virtual environment"
    fi

    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

    # Only prompt for configuration if not skipped
    if [ "$SKIP_CONFIG_PROMPTS" != "true" ]; then
        prompt_environment
        prompt_snipeit_config
        prompt_google_config
        prompt_gemini_config
    else
        print_info "Using existing configuration from .env file"
    fi

    create_env_file
    create_systemd_files
    validate_setup

    if [ $? -eq 0 ]; then
        print_next_steps
    else
        print_warning "Setup completed with warnings. Review above for details."
        exit 1
    fi
}

# Run main function
main "$@"
