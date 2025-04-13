pip install -r requirements.txt
# Index logs
python main.py index --log-file logs/fox_alerts.txt

# Search logs
python main.py search "suspicious DNS queries"

# Enrich logs
python main.py enrich
