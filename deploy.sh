#!/bin/bash

# 退出时终止所有子进程
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 打印带颜色的消息
print_message() {
    echo -e "${BLUE}[部署] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[成功] $1${NC}"
}

print_error() {
    echo -e "${RED}[错误] $1${NC}"
}

# 检查必要的命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装它"
        exit 1
    fi
}

check_command python3
check_command pip3
check_command nginx

# 项目目录
PROJECT_DIR=$(pwd)
APP_NAME="translator-api"
LOG_DIR="/var/log/$APP_NAME"
SYSTEMD_SERVICE="/etc/systemd/system/$APP_NAME.service"

# 创建虚拟环境
print_message "创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
print_message "安装项目依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 确保.env文件存在
if [ ! -f .env ]; then
    print_error ".env 文件不存在，请确保已配置环境变量"
    cp .env.example .env
    print_message "已创建 .env 文件，请编辑填写必要的环境变量后再继续"
    exit 1
fi

# 创建日志目录
print_message "创建日志目录..."
sudo mkdir -p $LOG_DIR
sudo chown $USER:$USER $LOG_DIR

# 创建systemd服务
print_message "创建systemd服务..."
sudo bash -c "cat > $SYSTEMD_SERVICE << EOF
[Unit]
Description=Multi-Language Translator API
After=network.target

[Service]
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 main:app
Restart=always
StandardOutput=append:$LOG_DIR/access.log
StandardError=append:$LOG_DIR/error.log
Environment=\"PATH=$PROJECT_DIR/venv/bin\"

[Install]
WantedBy=multi-user.target
EOF"

# 创建Nginx配置
print_message "创建Nginx配置..."
sudo bash -c "cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name _;  # 修改为您的域名

    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"

# 启用Nginx配置
print_message "启用Nginx配置..."
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo nginx -t

# 重启服务
print_message "启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl start $APP_NAME
sudo systemctl restart nginx

print_success "部署完成! API 服务已启动"
print_success "您可以访问以下地址查看API文档: http://your_server_ip/docs"
print_message "检查服务状态: sudo systemctl status $APP_NAME"
print_message "查看日志: sudo journalctl -u $APP_NAME -f" 