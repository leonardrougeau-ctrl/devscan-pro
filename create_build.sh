#!/bin/bash

# Configuration - USING CORRECT NAME
VERSION="1.0.0"
APP_NAME="devscan_pro"  # ← CHANGED TO MATCH YOUR APP
BUILD_DIR="build"
RELEASE_DIR="releases"
PACKAGE_NAME="${APP_NAME}-${VERSION}"

echo "🏗 Building ${APP_NAME} v${VERSION}..."
echo "📁 Source: $(pwd)"

# Clean previous builds
rm -rf "${BUILD_DIR}"
rm -f "${RELEASE_DIR}/${PACKAGE_NAME}.zip"

# Create directories
mkdir -p "${BUILD_DIR}/${PACKAGE_NAME}"
mkdir -p "${RELEASE_DIR}"

# Copy main application
echo "📄 Copying main application..."
cp src/devscan_pro.py "${BUILD_DIR}/${PACKAGE_NAME}/"

# Copy existing documentation
echo "📝 Copying documentation..."
cp README.md "${BUILD_DIR}/${PACKAGE_NAME}/" 2>/dev/null || true
cp docs/README.md "${BUILD_DIR}/${PACKAGE_NAME}/DOCUMENTATION.md" 2>/dev/null || true

# Copy requirements
echo "📦 Copying requirements..."
cp requirements.txt "${BUILD_DIR}/${PACKAGE_NAME}/" 2>/dev/null || true

# Copy license files if they exist
echo "⚖️ Copying license files..."
cp -r src/licenses "${BUILD_DIR}/${PACKAGE_NAME}/" 2>/dev/null || true

# Create essential files
echo "🛠 Creating installation scripts..."

# Create install script
cat > "${BUILD_DIR}/${PACKAGE_NAME}/install.sh" << 'INSTEOF'
#!/bin/bash
echo "🚀 Installing DevScan Pro v1.0.0"
echo "=================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install python3."
    exit 1
fi

# Check Tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "📦 Tkinter not found. Installing..."
    sudo apt update && sudo apt install python3-tk -y
fi

# Install dependencies if requirements exist
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Launch application
echo "🎯 Launching DevScan Pro..."
python3 devscan_pro.py
INSTEOF
chmod +x "${BUILD_DIR}/${PACKAGE_NAME}/install.sh"

# Create simple run script
cat > "${BUILD_DIR}/${PACKAGE_NAME}/run.sh" << 'RUNEOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 devscan_pro.py
RUNEOF
chmod +x "${BUILD_DIR}/${PACKAGE_NAME}/run.sh"

# Create quick start guide
cat > "${BUILD_DIR}/${PACKAGE_NAME}/QUICK_START.md" << 'QSEOF'
# DevScan Pro - Quick Start

## Installation
1. Run: `./install.sh`
2. Or manually: `python3 devscan_pro.py`

## System Requirements
- Ubuntu 18.04+ or compatible Linux
- Python 3.6+
- Tkinter

## Support
- Email: support@devscan.pro
- Website: https://devscan.pro
QSEOF

# Create package
echo "📦 Creating ZIP package..."
cd "${BUILD_DIR}"
zip -r "../${RELEASE_DIR}/${PACKAGE_NAME}.zip" "${PACKAGE_NAME}"

# Cleanup
cd ..
rm -rf "${BUILD_DIR}"

echo ""
echo "✅ BUILD SUCCESSFUL!"
echo "📦 Package: ${RELEASE_DIR}/${PACKAGE_NAME}.zip"
echo ""
echo "📊 Package contents:"
unzip -l "${RELEASE_DIR}/${PACKAGE_NAME}.zip"
