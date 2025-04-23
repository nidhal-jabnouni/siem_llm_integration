from src.application.dto.alert_dto import AlertDTO

def handle_threat(alert: AlertDTO):
    """Handle the threat alert received from the Detector Agent."""
    print(f"Reactor Agent received alert: {alert}")
    print("Starting response playbook...")
