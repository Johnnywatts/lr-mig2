#!/bin/bash
# Script to generate and scan test data in Docker

set -e  # Exit on error

cd "$(dirname "$0")/.." || exit 1

echo "==== Lightroom File Management Utility Test Data Generator ===="
echo

# Command options
CLEAN=""
VERBOSE=""
GROUP=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean|-c)
            CLEAN="--clean"
            shift
            ;;
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --group|-g)
            GROUP="--group $2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: docker/test-data.sh [options]"
            echo
            echo "Options:"
            echo "  --clean, -c            Clean existing test data before generating"
            echo "  --verbose, -v          Enable verbose output"
            echo "  --group, -g GROUP      Only scan directories from this group"
            echo "  --help, -h             Show this help message"
            echo
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker doesn't seem to be running. Please start Docker and try again."
    exit 1
fi

# Check if containers are built
if ! docker-compose ps -q app > /dev/null 2>&1; then
    echo "Building Docker containers..."
    docker-compose build
fi

# Step 1: Generate test data
echo "Generating test data..."
docker-compose run --rm app python tests/generate_test_data.py $CLEAN

# Step 2: Run test scan
echo
echo "Running test scan..."
docker-compose run --rm app python tests/run_test_scan.py $VERBOSE $GROUP

echo
echo "✅ Test completed successfully!" 