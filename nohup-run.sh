#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 打印带颜色的消息
print_message() {
    echo -e "${BLUE}[信息] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[成功] $1${NC}"
}

print_error() {
    echo -e "${RED}[错误] $1${NC}"
}

# 检查Python和pip是否安装
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装它"
        exit 1
    fi
}

check_command python3
check_command pip3

# 项目目录
PROJECT_DIR=$(pwd)
LOG_FILE="$PROJECT_DIR/app.log"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    print_message "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
print_message "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
print_message "安装依赖..."
pip install -r requirements.txt

# 检查.env文件
if [ ! -f .env ]; then
    print_error ".env 文件不存在，将使用示例配置文件"
    cp .env.example .env
    print_message "已创建 .env 文件，请编辑填写必要的环境变量后再继续"
    exit 1
fi

# 检查应用是否已在运行
PID=$(pgrep -f "python -m uvicorn main:app")
if [ ! -z "$PID" ]; then
    print_message "应用已在运行，PID: $PID"
    print_message "正在停止旧进程..."
    kill $PID
    sleep 2
fi

# 启动应用
print_success "所有准备工作已完成，在后台启动应用..."
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > $LOG_FILE 2>&1 &

# 保存PID
PID=$!
echo $PID > "$PROJECT_DIR/app.pid"

print_success "应用已在后台启动，PID: $PID"
print_message "日志文件: $LOG_FILE"
print_message "查看日志: tail -f $LOG_FILE"
print_message "停止应用: kill \$(cat $PROJECT_DIR/app.pid)"
print_message "API地址: http://$(hostname -I | awk '{print $1}'):8000"
print_message "API文档: http://$(hostname -I | awk '{print $1}'):8000/docs" 