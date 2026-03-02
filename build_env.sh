#!/bin/bash

# 颜色定义 | Color Definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息 | Print colored messages
print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# 打印标题 | Print Title
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    Storyline 项目依赖安装脚本 | Dependency Installation       ║"
echo "║    使用 conda activate storyline 激活环境后运行                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ==========================================
# 步骤 0: 检测操作系统
# Step 0: Detect OS
# ==========================================
print_info "检测操作系统... | Detecting OS..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    IS_MACOS=true
    IS_LINUX=false
    print_success "检测到 MacOS 系统 | MacOS detected"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    IS_MACOS=false
    IS_LINUX=true
    print_success "检测到 Linux 系统 | Linux detected"
else
    print_error "不支持的操作系统 | Unsupported operating system: $OSTYPE"
    exit 1
fi
echo ""

# ==========================================
# 步骤 1: 检查 conda 环境
# Step 1: Check conda environment
# ==========================================
echo "[1/4] 检查 conda 环境... | Checking conda environment..."

if [ -z "$CONDA_DEFAULT_ENV" ]; then
    print_error "未检测到 conda 环境 | No conda environment detected"
    echo ""
    echo "请先运行: conda activate storyline"
    echo "Please run: conda activate storyline"
    exit 1
fi

if [ "$CONDA_DEFAULT_ENV" != "storyline" ]; then
    print_warning "当前环境: $CONDA_DEFAULT_ENV"
    echo ""
    read -p "建议使用 storyline 环境，是否继续? | Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "请运行: conda activate storyline"
        exit 1
    fi
else
    print_success "当前环境: storyline"
fi

# 显示 Python 信息
print_info "Python 信息 | Python Info:"
echo "  版本 | Version: $(python --version 2>&1)"
echo "  路径 | Path: $(which python)"
echo ""

# ==========================================
# 步骤 2: 检查 FFmpeg
# Step 2: Check FFmpeg
# ==========================================
echo "[2/4] 检查 FFmpeg... | Checking FFmpeg..."

if ! command -v ffmpeg &> /dev/null; then
    print_warning "未检测到 FFmpeg | FFmpeg not detected"
    echo ""
    
    read -p "是否安装 FFmpeg? | Install FFmpeg? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "正在安装 FFmpeg... | Installing FFmpeg..."
        
        if [ "$IS_MACOS" = true ]; then
            if ! command -v brew &> /dev/null; then
                print_error "需要 Homebrew 来安装 FFmpeg | Homebrew required to install FFmpeg"
                echo "请访问: https://brew.sh"
                exit 1
            fi
            brew install ffmpeg
        elif [ "$IS_LINUX" = true ]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y ffmpeg
            elif command -v yum &> /dev/null; then
                sudo yum install -y epel-release
                sudo yum install -y ffmpeg ffmpeg-devel
            else
                print_error "无法识别的包管理器 | Unrecognized package manager"
                exit 1
            fi
        fi
        
        if [ $? -eq 0 ]; then
            print_success "FFmpeg 安装成功 | FFmpeg installed successfully"
        else
            print_error "FFmpeg 安装失败 | FFmpeg installation failed"
            exit 1
        fi
    else
        print_warning "跳过 FFmpeg 安装（可能影响音视频处理功能）"
        print_warning "Skipping FFmpeg (may affect audio/video features)"
    fi
else
    print_success "FFmpeg 已安装 | FFmpeg installed"
    echo "  版本 | Version: $(ffmpeg -version 2>&1 | head -n 1)"
fi
echo ""

# ==========================================
# 步骤 3: 下载项目资源
# Step 3: Download project resources
# ==========================================
echo "[3/4] 下载项目资源... | Downloading project resources..."

if [ -f "download.sh" ]; then
    print_info "执行资源下载脚本... | Running download script..."
    chmod +x download.sh
    ./download.sh
    
    if [ $? -eq 0 ]; then
        print_success "资源下载完成 | Resources downloaded successfully"
    else
        print_error "资源下载失败 | Resource download failed"
        exit 1
    fi
else
    print_warning "未找到 download.sh | download.sh not found"
    echo "如需下载模型等资源，请手动执行 download.sh"
    echo "To download models, please run download.sh manually"
fi
echo ""

# ==========================================
# 步骤 4: 安装 Python 依赖
# Step 4: Install Python dependencies
# ==========================================
echo "[4/4] 安装 Python 依赖... | Installing Python dependencies..."

if [ ! -f "requirements.txt" ]; then
    print_error "未找到 requirements.txt | requirements.txt not found"
    exit 1
fi

print_info "正在安装依赖包，请稍候... | Installing packages, please wait..."
echo ""

# 安装依赖
print_info "安装依赖包... | Installing dependencies..."

# 尝试使用清华镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if [ $? -ne 0 ]; then
    print_warning "清华镜像安装失败，尝试使用默认源... | Tsinghua mirror failed, trying default..."
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        print_error "依赖安装失败 | Dependency installation failed"
        echo ""
        echo "请尝试手动安装: pip install -r requirements.txt"
        exit 1
    fi
fi

print_success "依赖安装完成 | Dependencies installed successfully"
echo ""

# ==========================================
# 安装完成 | Installation Complete
# ==========================================
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          安装成功！| Installation Successful!                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

print_info "环境信息 | Environment Info:"
echo "  Conda 环境 | Conda Env: $CONDA_DEFAULT_ENV"
echo "  Python: $(python --version 2>&1)"
command -v ffmpeg &> /dev/null && echo "  FFmpeg: $(ffmpeg -version 2>&1 | head -n 1 | cut -d' ' -f3)"
echo ""

print_success "现在可以运行项目了！| You can now run the project!"
