import time
from src.application.dto.alert_dto import AlertDTO
from src.infrastructure.messaging.signals import threat_detected


class DetectorAgent:
    def __init__(self):
        self.log_counter = 0

    def fetch_log(self):
        """Simulate fetching a log from Wazuh."""
        self.log_counter += 1
        return {
            "log_id": f"log_{self.log_counter}",
            "timestamp": "2023-10-01T12:00:00Z",
            "source_ip": "192.168.1.100",
            "raw_data": f"Login attempt {self.log_counter}"
        }

    def simplify_log(self, log_data):
        """Simplify the log for processing."""
        return {
            "log_id": log_data["log_id"],
            "timestamp": log_data["timestamp"],
            "source_ip": log_data["source_ip"],
            "details": f"Simplified: {log_data['raw_data']}"
        }

    def classify_threat(self, simplified_log):
        """Simulate threat classification (e.g., benign, suspicious, attack)."""
        # For simplicity, classify every 3rd log as suspicious, every 5th as attack
        log_num = int(simplified_log["log_id"].split("_")[1])
        if log_num % 5 == 0:
            return "attack"
        elif log_num % 3 == 0:
            return "suspicious"
        return "benign"

    def create_alert(self, simplified_log, threat_level):
        """Create an AlertDTO for suspicious or attack threats."""
        return AlertDTO(
            log_id=simplified_log["log_id"],
            threat_level=threat_level,
            timestamp=simplified_log["timestamp"],
            source_ip=simplified_log["source_ip"],
            details=simplified_log["details"]
        )

    def start(self):
        """Start the log processing loop."""
        print("Detector Agent started...")
        while True:
            log_data = self.fetch_log()
            simplified_log = self.simplify_log(log_data)
            threat_level = self.classify_threat(simplified_log)
            print(f"Classified log {simplified_log['log_id']} as {threat_level}")

            if threat_level in ["suspicious", "attack"]:
                alert = self.create_alert(simplified_log, threat_level)
                print(f"Detector Agent sending alert: {alert}")
                threat_detected.send(alert)

            time.sleep(1)  # Simulate delay between logs


if __name__ == "__main__":
    agent = DetectorAgent()
    agent.start()