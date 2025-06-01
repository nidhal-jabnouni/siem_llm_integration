# src/infrastructure/agents/reactor/tools.py
from langchain.tools import BaseTool
from typing import Optional, Dict, Any
import datetime
import json
import re


class BlockIPTool(BaseTool):
    """Tool for blocking malicious IP addresses via firewall"""
    name: str = "block_ip"
    description: str = "Block malicious IP addresses via firewall rules. Input should be a valid IP address."

    def _run(self, ip_address: str) -> str:
        # Validate IP address format
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

        if not re.match(ip_pattern, ip_address.strip()):
            return f"❌ Invalid IP address format: {ip_address}"

        # Simulate firewall blocking
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "action": "block_ip",
            "ip_address": ip_address.strip(),
            "status": "success",
            "timestamp": timestamp,
            "method": "firewall_rule",
            "rule_id": f"BLOCK_{ip_address.replace('.', '_')}_{int(datetime.datetime.now().timestamp())}"
        }

        return f"✅ Successfully blocked IP {ip_address} in firewall\n" \
               f"Rule ID: {result['rule_id']}\n" \
               f"Timestamp: {timestamp}\n" \
               f"Status: Active"


class GenerateAlertTool(BaseTool):
    """Tool for creating security alerts for SOC team"""
    name: str = "generate_alert"
    description: str = "Create security alert for SOC team. Requires message and optional severity (low, medium, high, critical)."

    def _run(self, message: str, severity: str = "medium", ) -> str:
        # Validate severity level
        valid_severities = ["low", "medium", "high", "critical"]
        severity = severity.lower().strip()

        if severity not in valid_severities:
            severity = "medium"

        # Generate alert
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_id = f"SEC_{int(datetime.datetime.now().timestamp())}"

        alert = {
            "alert_id": alert_id,
            "severity": severity.upper(),
            "details": message,
            "timestamp": timestamp,
            "status": "open",
            "assigned_to": "SOC_TEAM",
            "priority": self._get_priority_score(severity)
        }

        return f"🚨 Security Alert Created\n" \
               f"Alert ID: {alert_id}\n" \
               f"Severity: {severity.upper()}\n" \
               f"Details: {message}\n" \
               f"Timestamp: {timestamp}\n" \
               f"Priority Score: {alert['priority']}/10\n" \
               f"Status: OPEN - Assigned to SOC Team"

    def _get_priority_score(self, severity: str) -> int:
        """Convert severity to priority score"""
        priority_map = {
            "low": 3,
            "medium": 5,
            "high": 8,
            "critical": 10
        }
        return priority_map.get(severity, 5)


class CreateAndExecuteScriptTool(BaseTool):
    """Tool for generating and running scripts to resolve security issues"""
    name: str = "execute_script"
    description: str = "Generate and run scripts to resolve security issues. Input should describe the security issue to be resolved."

    def _run(self, enriched_input: str) -> str:
        # Analyze the input to determine script type
        script_type = self._determine_script_type(enriched_input)
        script_content = self._generate_script(enriched_input, script_type)

        # Simulate script execution
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execution_id = f"EXEC_{int(datetime.datetime.now().timestamp())}"

        result = {
            "execution_id": execution_id,
            "script_type": script_type,
            "input_issue": enriched_input[:100] + "..." if len(enriched_input) > 100 else enriched_input,
            "timestamp": timestamp,
            "status": "completed",
            "exit_code": 0
        }

        return f"🔧 Security Script Executed\n" \
               f"Execution ID: {execution_id}\n" \
               f"Script Type: {script_type}\n" \
               f"Issue: {result['input_issue']}\n" \
               f"Timestamp: {timestamp}\n" \
               f"Status: COMPLETED\n" \
               f"Exit Code: 0\n" \
               f"Generated Script:\n{script_content}"

    def _determine_script_type(self, issue: str) -> str:
        """Determine the type of script needed based on the issue"""
        issue_lower = issue.lower()

        if any(word in issue_lower for word in ["malware", "virus", "infection"]):
            return "malware_removal"
        elif any(word in issue_lower for word in ["firewall", "block", "ip"]):
            return "firewall_config"
        elif any(word in issue_lower for word in ["user", "account", "access"]):
            return "user_management"
        elif any(word in issue_lower for word in ["backup", "restore"]):
            return "backup_recovery"
        elif any(word in issue_lower for word in ["log", "audit", "monitoring"]):
            return "log_analysis"
        else:
            return "general_security"

    def _generate_script(self, issue: str, script_type: str) -> str:
        """Generate appropriate script content based on issue type"""
        scripts = {
            "malware_removal": """#!/bin/bash
# Malware Removal Script
echo "Starting malware scan..."
sudo clamscan -r /home --remove
sudo rkhunter --check --skip-keypress
echo "Malware scan completed"
""",
            "firewall_config": """#!/bin/bash
# Firewall Configuration Script
echo "Updating firewall rules..."
sudo ufw status
sudo ufw deny from suspicious_ip
sudo ufw reload
echo "Firewall rules updated"
""",
            "user_management": """#!/bin/bash
# User Account Management Script
echo "Managing user accounts..."
sudo passwd -l suspicious_user
sudo usermod -s /bin/false suspicious_user
echo "User account secured"
""",
            "backup_recovery": """#!/bin/bash
# Backup and Recovery Script
echo "Initiating backup process..."
sudo rsync -av /important_data/ /backup/
sudo systemctl restart backup-service
echo "Backup process completed"
""",
            "log_analysis": """#!/bin/bash
# Log Analysis Script
echo "Analyzing system logs..."
sudo grep -i "error\|warning\|failed" /var/log/syslog | tail -20
sudo journalctl --since "1 hour ago" --priority=err
echo "Log analysis completed"
""",
            "general_security": """#!/bin/bash
# General Security Script
echo "Running security checks..."
sudo netstat -tuln
sudo ps aux | grep -v grep
sudo find /tmp -type f -atime +7 -delete
echo "Security checks completed"
"""
        }

        return scripts.get(script_type, scripts["general_security"])


class IsolateHostTool(BaseTool):
    """Tool for isolating compromised hosts from the network"""
    name: str = "isolate_host"
    description: str = "Isolate a compromised host from the network. Input should be the hostname or IP address."

    def _run(self, hostname: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        isolation_id = f"ISO_{int(datetime.datetime.now().timestamp())}"

        return f"🔒 Host Isolation Executed\n" \
               f"Isolation ID: {isolation_id}\n" \
               f"Host: {hostname}\n" \
               f"Timestamp: {timestamp}\n" \
               f"Status: ISOLATED\n" \
               f"Network Access: DISABLED\n" \
               f"Remote Management: ENABLED"


# Tool registry for easy access
SECURITY_TOOLS = [
    BlockIPTool(),
    GenerateAlertTool(),
    CreateAndExecuteScriptTool(),
    IsolateHostTool()
]


def get_all_tools():
    """Return all available security tools"""
    return SECURITY_TOOLS


def get_tool_by_name(tool_name: str):
    """Get a specific tool by name"""
    for tool in SECURITY_TOOLS:
        if tool.name == tool_name:
            return tool
    return None


# Test function for manual verification
if __name__ == "__main__":
    print("Testing Security Tools:")
    print("=" * 50)

    # Test BlockIPTool
    block_tool = BlockIPTool()
    print("1. Testing BlockIPTool:")
    print(block_tool.run("192.168.1.100"))
    print()

    # Test GenerateAlertTool
    alert_tool = GenerateAlertTool()
    print("2. Testing GenerateAlertTool:")
    print(alert_tool.run("Suspicious network activity detected", "high"))
    print()

    # Test CreateAndExecuteScriptTool
    script_tool = CreateAndExecuteScriptTool()
    print("3. Testing CreateAndExecuteScriptTool:")
    print(script_tool.run("Malware detected on server"))
    print()

    # Test IsolateHostTool
    isolate_tool = IsolateHostTool()
    print("4. Testing IsolateHostTool:")
    print(isolate_tool.run("WEB-SERVER-01"))