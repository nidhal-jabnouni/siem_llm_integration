from src.infrastructure.agents.anomaly_detection import DetectorAgent
from src.infrastructure.agents.response_playbook import handle_threat
from src.infrastructure.messaging.signals import threat_detected


def main():
    detector_agent = DetectorAgent()

    threat_detected.connect(handle_threat)
    print("Notification system initialized.")

    detector_agent.start()


if __name__ == "__main__":
    main()