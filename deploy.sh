#!/bin/bash

###############################################################################
# Google Calendar Reminder Service - 部署脚本
# 用途：在 Linux 系统上部署日历提醒服务
# 功能：
#   - 安装 Python 依赖
#   - 配置 systemd 服务
#   - 设置开机自启动
#   - 自动健康检查和重启
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
INSTALL_DIR="/opt/calendar-reminder"
SERVICE_NAME="calendar-reminder"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_FILE="/var/log/${SERVICE_NAME}.log"
ERROR_LOG_FILE="/var/log/${SERVICE_NAME}.error.log"

# 函数：打印信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：检查是否以 root 运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要 root 权限运行"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 函数：检查 Python 版本
check_python() {
    print_info "检查 Python 版本..."

    if ! command -v python3 &> /dev/null; then
        print_error "未找到 python3，请先安装 Python 3"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_info "Python 版本: $PYTHON_VERSION"
}

# 函数：检查 pip
check_pip() {
    print_info "检查 pip..."

    if ! command -v pip3 &> /dev/null; then
        print_warning "未找到 pip3，正在安装..."
        apt-get update
        apt-get install -y python3-pip
    fi
}

# 函数：创建安装目录
create_install_dir() {
    print_info "创建安装目录: $INSTALL_DIR"

    # 使用全局变量记录备份目录
    BACKUP_DIR=""

    if [ -d "$INSTALL_DIR" ]; then
        print_warning "目录已存在，将备份现有文件..."
        BACKUP_DIR="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        print_info "已备份到: $BACKUP_DIR"
    fi

    mkdir -p "$INSTALL_DIR"
}

# 函数：复制文件
copy_files() {
    print_info "复制程序文件到 $INSTALL_DIR"

    # 获取当前脚本所在目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

    # 复制必要的文件
    cp "$SCRIPT_DIR/main_cli.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/google_calendar_cli.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/home_assistant.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

    # 复制 .env.example（始终复制，作为参考）
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/"
        print_info "已复制 .env.example（配置参考）"
    fi

    # 恢复或复制 .env 配置文件（优先从备份恢复）
    if [ -n "$BACKUP_DIR" ] && [ -f "$BACKUP_DIR/.env" ]; then
        cp "$BACKUP_DIR/.env" "$INSTALL_DIR/"
        print_info "已从备份恢复 .env 文件"
    elif [ -f "$SCRIPT_DIR/.env" ]; then
        cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/"
        print_info "已复制 .env 文件"
    else
        print_warning ".env 文件不存在，请基于 .env.example 创建并配置"
    fi

    # 恢复或复制 credentials.json（优先从备份恢复）
    if [ -n "$BACKUP_DIR" ] && [ -f "$BACKUP_DIR/credentials.json" ]; then
        cp "$BACKUP_DIR/credentials.json" "$INSTALL_DIR/"
        print_info "已从备份恢复 credentials.json"
    elif [ -f "$SCRIPT_DIR/credentials.json" ]; then
        cp "$SCRIPT_DIR/credentials.json" "$INSTALL_DIR/"
        print_info "已复制 credentials.json"
    else
        print_warning "credentials.json 不存在，请稍后手动配置"
    fi

    # 恢复或复制 token.pickle（优先从备份恢复）
    if [ -n "$BACKUP_DIR" ] && [ -f "$BACKUP_DIR/token.pickle" ]; then
        cp "$BACKUP_DIR/token.pickle" "$INSTALL_DIR/"
        print_info "已从备份恢复 token.pickle (Google 认证令牌)"
    elif [ -f "$SCRIPT_DIR/token.pickle" ]; then
        cp "$SCRIPT_DIR/token.pickle" "$INSTALL_DIR/"
        print_info "已复制 token.pickle (Google 认证令牌)"
    fi

    # 恢复或复制 reminded_events.json（优先从备份恢复）
    if [ -n "$BACKUP_DIR" ] && [ -f "$BACKUP_DIR/reminded_events.json" ]; then
        cp "$BACKUP_DIR/reminded_events.json" "$INSTALL_DIR/"
        print_info "已从备份恢复 reminded_events.json (提醒记录)"
    elif [ -f "$SCRIPT_DIR/reminded_events.json" ]; then
        cp "$SCRIPT_DIR/reminded_events.json" "$INSTALL_DIR/"
        print_info "已复制 reminded_events.json (提醒记录)"
    fi
}

# 函数：安装 Python 依赖
install_dependencies() {
    print_info "安装 Python 依赖..."

    cd "$INSTALL_DIR"
    pip3 install -r requirements.txt

    print_info "依赖安装完成"
}

# 函数：配置 systemd 服务
setup_systemd() {
    print_info "配置 systemd 服务..."

    # 创建服务文件
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Google Calendar Reminder Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=/usr/bin/python3 $INSTALL_DIR/main_cli.py --headless
Restart=always
RestartSec=10
StandardOutput=append:$LOG_FILE
StandardError=append:$ERROR_LOG_FILE

# 环境变量
Environment="PYTHONUNBUFFERED=1"

# 健康检查和资源限制
TimeoutStopSec=30
MemoryLimit=500M

[Install]
WantedBy=multi-user.target
EOF

    print_info "服务文件已创建: $SERVICE_FILE"
}

# 函数：创建日志文件
setup_logs() {
    print_info "设置日志文件..."

    touch "$LOG_FILE"
    touch "$ERROR_LOG_FILE"
    chmod 644 "$LOG_FILE"
    chmod 644 "$ERROR_LOG_FILE"

    print_info "日志文件:"
    print_info "  - 标准输出: $LOG_FILE"
    print_info "  - 错误输出: $ERROR_LOG_FILE"
}

# 函数：启动服务
start_service() {
    print_info "重新加载 systemd 配置..."
    systemctl daemon-reload

    print_info "启用服务（开机自启动）..."
    systemctl enable "$SERVICE_NAME"

    print_info "启动服务..."
    systemctl start "$SERVICE_NAME"

    sleep 2

    print_info "服务状态:"
    systemctl status "$SERVICE_NAME" --no-pager || true
}

# 函数：显示部署信息
show_deployment_info() {
    echo ""
    echo "=========================================="
    print_info "部署完成！"
    echo "=========================================="
    echo ""
    echo "服务管理命令:"
    echo "  - 查看状态:   sudo systemctl status $SERVICE_NAME"
    echo "  - 停止服务:   sudo systemctl stop $SERVICE_NAME"
    echo "  - 启动服务:   sudo systemctl start $SERVICE_NAME"
    echo "  - 重启服务:   sudo systemctl restart $SERVICE_NAME"
    echo "  - 查看日志:   sudo journalctl -u $SERVICE_NAME -f"
    echo "  - 查看日志文件: tail -f $LOG_FILE"
    echo ""
    echo "文件位置:"
    echo "  - 安装目录:   $INSTALL_DIR"
    echo "  - 服务配置:   $SERVICE_FILE"
    echo "  - 日志文件:   $LOG_FILE"
    echo "  - 错误日志:   $ERROR_LOG_FILE"
    echo ""
    print_warning "请确保已正确配置以下文件:"
    echo "  - $INSTALL_DIR/.env (环境变量配置)"
    echo "  - $INSTALL_DIR/credentials.json (Google API 凭证)"
    echo ""
    print_info "如需卸载服务，请运行: sudo ./uninstall.sh"
    echo "=========================================="
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  Google Calendar Reminder - 部署脚本"
    echo "=========================================="
    echo ""

    check_root
    check_python
    check_pip
    create_install_dir
    copy_files
    install_dependencies
    setup_systemd
    setup_logs
    start_service
    show_deployment_info
}

# 执行主函数
main
