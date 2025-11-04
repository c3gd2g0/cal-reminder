#!/bin/bash

###############################################################################
# Google Calendar Reminder Service - 卸载脚本
# 用途：从系统中完全移除日历提醒服务
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

# 函数：停止并禁用服务
stop_service() {
    print_info "停止服务..."

    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        print_info "服务已停止"
    else
        print_warning "服务未在运行"
    fi

    print_info "禁用开机自启动..."
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        systemctl disable "$SERVICE_NAME"
        print_info "已禁用开机自启动"
    else
        print_warning "服务未启用"
    fi
}

# 函数：删除服务文件
remove_service_file() {
    print_info "删除 systemd 服务文件..."

    if [ -f "$SERVICE_FILE" ]; then
        rm -f "$SERVICE_FILE"
        print_info "服务文件已删除: $SERVICE_FILE"

        print_info "重新加载 systemd 配置..."
        systemctl daemon-reload
        systemctl reset-failed
    else
        print_warning "服务文件不存在: $SERVICE_FILE"
    fi
}

# 函数：询问是否删除安装目录
remove_install_dir() {
    if [ -d "$INSTALL_DIR" ]; then
        echo ""
        print_warning "是否删除安装目录 $INSTALL_DIR ?"
        print_warning "这将删除所有程序文件、配置文件和状态数据"
        read -p "输入 yes 确认删除: " -r
        echo

        if [[ $REPLY == "yes" ]]; then
            # 备份重要文件
            BACKUP_DIR="${INSTALL_DIR}.uninstall.backup.$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$BACKUP_DIR"

            # 备份配置和数据文件
            [ -f "$INSTALL_DIR/.env" ] && cp "$INSTALL_DIR/.env" "$BACKUP_DIR/"
            [ -f "$INSTALL_DIR/credentials.json" ] && cp "$INSTALL_DIR/credentials.json" "$BACKUP_DIR/"
            [ -f "$INSTALL_DIR/token.pickle" ] && cp "$INSTALL_DIR/token.pickle" "$BACKUP_DIR/"
            [ -f "$INSTALL_DIR/reminded_events.json" ] && cp "$INSTALL_DIR/reminded_events.json" "$BACKUP_DIR/"

            print_info "重要文件已备份到: $BACKUP_DIR"

            # 删除安装目录
            rm -rf "$INSTALL_DIR"
            print_info "安装目录已删除"
        else
            print_info "保留安装目录: $INSTALL_DIR"
        fi
    else
        print_warning "安装目录不存在: $INSTALL_DIR"
    fi
}

# 函数：询问是否删除日志
remove_logs() {
    echo ""
    print_warning "是否删除日志文件？"
    read -p "输入 yes 确认删除: " -r
    echo

    if [[ $REPLY == "yes" ]]; then
        [ -f "$LOG_FILE" ] && rm -f "$LOG_FILE" && print_info "已删除: $LOG_FILE"
        [ -f "$ERROR_LOG_FILE" ] && rm -f "$ERROR_LOG_FILE" && print_info "已删除: $ERROR_LOG_FILE"
    else
        print_info "保留日志文件"
    fi
}

# 函数：显示卸载完成信息
show_uninstall_info() {
    echo ""
    echo "=========================================="
    print_info "卸载完成！"
    echo "=========================================="
    echo ""

    if [ -d "$INSTALL_DIR" ]; then
        print_info "安装目录保留在: $INSTALL_DIR"
    fi

    if [ -f "$LOG_FILE" ] || [ -f "$ERROR_LOG_FILE" ]; then
        print_info "日志文件:"
        [ -f "$LOG_FILE" ] && echo "  - $LOG_FILE"
        [ -f "$ERROR_LOG_FILE" ] && echo "  - $ERROR_LOG_FILE"
    fi

    echo ""
    print_info "如需重新安装，请运行: sudo ./deploy.sh"
    echo "=========================================="
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  Google Calendar Reminder - 卸载脚本"
    echo "=========================================="
    echo ""

    check_root
    stop_service
    remove_service_file
    remove_install_dir
    remove_logs
    show_uninstall_info
}

# 执行主函数
main
