#!/bin/bash
# ssl-cert-check.sh — SSL 证书到期检测
# 检测 Caddy 本地证书、Let's Encrypt、acme.sh 管理的证书
# 合并到早检/晚检使用，也可独立调用

set -euo pipefail

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")
WARN_DAYS=30
CRITICAL_DAYS=7

echo "=========================================="
echo "  SSL 证书检测 — $TIMESTAMP"
echo "=========================================="

CERT_FOUND=0
ISSUES_FOUND=0

# 1. Caddy 本地证书
CADDY_CERT_DIR="/var/lib/caddy/.local/share/caddy/certificates"
if [ -d "$CADDY_CERT_DIR" ]; then
    CERT_FOUND=$((CERT_FOUND + 1))
    echo ""
    echo "[Caddy Local Certificates]"
    
    find "$CADDY_CERT_DIR" -name "*.crt" -type f 2>/dev/null | while read -r cert_file; do
        # 从路径提取域名
        domain=$(echo "$cert_file" | sed "s|$CADDY_CERT_DIR/local/||" | sed 's|/.*||')
        
        if [ -n "$domain" ] && [ "$domain" != "$cert_file" ]; then
            expiry=$(openssl x509 -noout -enddate -in "$cert_file" 2>/dev/null | cut -d= -f2)
            if [ -n "$expiry" ]; then
                expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo 0)
                now_epoch=$(date +%s)
                remaining_days=$(( (expiry_epoch - now_epoch) / 86400 ))
                
                if [ "$remaining_days" -lt 0 ]; then
                    echo "  🔴 $domain: 已过期 ($expiry)"
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                elif [ "$remaining_days" -lt "$CRITICAL_DAYS" ]; then
                    echo "  🔴 $domain: 剩余 ${remaining_days} 天 ($expiry)"
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                elif [ "$remaining_days" -lt "$WARN_DAYS" ]; then
                    echo "  🟡 $domain: 剩余 ${remaining_days} 天 ($expiry)"
                else
                    echo "  🟢 $domain: 剩余 ${remaining_days} 天 ($expiry)"
                fi
            fi
        fi
    done
fi

# 2. Let's Encrypt 证书
LE_DIR="/etc/letsencrypt/live"
if [ -d "$LE_DIR" ]; then
    for domain_dir in "$LE_DIR"/*/; do
        [ -d "$domain_dir" ] || continue
        CERT_FOUND=$((CERT_FOUND + 1))
        domain=$(basename "$domain_dir")
        cert_path="$domain_dir/fullchain.pem"
        
        if [ -f "$cert_path" ]; then
            expiry=$(openssl x509 -noout -enddate -in "$cert_path" 2>/dev/null | cut -d= -f2)
            if [ -n "$expiry" ]; then
                expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo 0)
                now_epoch=$(date +%s)
                remaining_days=$(( (expiry_epoch - now_epoch) / 86400 ))
                
                if [ "$remaining_days" -lt 0 ]; then
                    echo "  🔴 $domain (LE): 已过期"
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                elif [ "$remaining_days" -lt "$CRITICAL_DAYS" ]; then
                    echo "  🔴 $domain (LE): 剩余 ${remaining_days} 天"
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                elif [ "$remaining_days" -lt "$WARN_DAYS" ]; then
                    echo "  🟡 $domain (LE): 剩余 ${remaining_days} 天"
                else
                    echo "  🟢 $domain (LE): 剩余 ${remaining_days} 天"
                fi
            fi
        fi
    done
fi

# 3. acme.sh 证书
ACME_DIR_ROOT="/root/.acme.sh"
if [ -d "$ACME_DIR_ROOT" ]; then
    for domain_dir in "$ACME_DIR_ROOT"/*/; do
        [ -d "$domain_dir" ] || continue
        domain=$(basename "$domain_dir")
        cert_path="$domain_dir/${domain}.cer"
        
        if [ -f "$cert_path" ]; then
            CERT_FOUND=$((CERT_FOUND + 1))
            expiry=$(openssl x509 -noout -enddate -in "$cert_path" 2>/dev/null | cut -d= -f2)
            if [ -n "$expiry" ]; then
                expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo 0)
                now_epoch=$(date +%s)
                remaining_days=$(( (expiry_epoch - now_epoch) / 86400 ))
                
                if [ "$remaining_days" -lt 0 ]; then
                    echo "  🔴 $domain (acme.sh): 已过期"
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                elif [ "$remaining_days" -lt "$CRITICAL_DAYS" ]; then
                    echo "  🔴 $domain (acme.sh): 剩余 ${remaining_days} 天"
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                elif [ "$remaining_days" -lt "$WARN_DAYS" ]; then
                    echo "  🟡 $domain (acme.sh): 剩余 ${remaining_days} 天"
                else
                    echo "  🟢 $domain (acme.sh): 剩余 ${remaining_days} 天"
                fi
            fi
        fi
    done
fi

# 4. OpenClaw 本地证书
OPENCLAW_CERT_DIR="/home/ubuntu/.openclaw/certs"
if [ -d "$OPENCLAW_CERT_DIR" ]; then
    CERT_FOUND=$((CERT_FOUND + 1))
    echo ""
    echo "[OpenClaw Local Certificates]"
    
    find "$OPENCLAW_CERT_DIR" -name "*.crt" -type f 2>/dev/null | while read -r cert_file; do
        domain=$(basename "$cert_file" .crt)
        expiry=$(openssl x509 -noout -enddate -in "$cert_file" 2>/dev/null | cut -d= -f2)
        if [ -n "$expiry" ]; then
            expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo 0)
            now_epoch=$(date +%s)
            remaining_days=$(( (expiry_epoch - now_epoch) / 86400 ))
            
            if [ "$remaining_days" -lt 0 ]; then
                echo "  🔴 $domain: 已过期 ($expiry)"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            elif [ "$remaining_days" -lt "$CRITICAL_DAYS" ]; then
                echo "  🔴 $domain: 剩余 ${remaining_days} 天 ($expiry)"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            elif [ "$remaining_days" -lt "$WARN_DAYS" ]; then
                echo "  🟡 $domain: 剩余 ${remaining_days} 天 ($expiry)"
            else
                echo "  🟢 $domain: 剩余 ${remaining_days} 天 ($expiry)"
            fi
        fi
    done
fi

# 5. 通用 PEM/CRT 文件扫描（排除系统 CA）
echo ""
echo "[通用证书扫描]"
FOUND_GENERIC=0
while IFS= read -r cert_file; do
    # 跳过系统 CA 证书
    echo "$cert_file" | grep -qE "/etc/ssl/certs/|^/usr/" && continue
    
    domain=$(basename "$cert_file" .crt 2>/dev/null || echo "unknown")
    expiry=$(openssl x509 -noout -enddate -in "$cert_file" 2>/dev/null | cut -d= -f2 || true)
    
    if [ -n "$expiry" ]; then
        FOUND_GENERIC=1
        CERT_FOUND=$((CERT_FOUND + 1))
        expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo 0)
        now_epoch=$(date +%s)
        remaining_days=$(( (expiry_epoch - now_epoch) / 86400 ))
        
        if [ "$remaining_days" -lt 0 ]; then
            echo "  🔴 $cert_file: 已过期"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        elif [ "$remaining_days" -lt "$WARN_DAYS" ]; then
            echo "  🟡 $cert_file: 剩余 ${remaining_days} 天"
        else
            echo "  🟢 $cert_file: 剩余 ${remaining_days} 天"
        fi
    fi
done < <(find /etc /opt /home /root -name "*.pem" -o -name "*.crt" 2>/dev/null | grep -vE "/etc/ssl/certs/|/usr/share|/usr/lib" | head -20)

if [ "$FOUND_GENERIC" -eq 0 ]; then
    echo "  未发现额外证书"
fi

# 总结
echo ""
echo "=========================================="
echo "  检测结果: 共检测 $CERT_FOUND 个证书"
if [ "$ISSUES_FOUND" -gt 0 ]; then
    echo "  ⚠️  发现 $ISSUES_FOUND 个问题证书"
else
    echo "  ✅ 所有证书正常"
fi
echo "=========================================="

# 返回退出码供上游判断
if [ "$ISSUES_FOUND" -gt 0 ]; then
    exit 1
fi
exit 0
