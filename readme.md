SIEM LLM Integration - Security Threat Detector & Logs Enricher
This project processes Wazuh SIEM data to enrich logs and detect security threats.

🚀 Getting Started
Follow these steps to set up and run the application.

1. Clone the Repository
Clone the repository to your local machine:

bash
Copier
Modifier
git clone https://github.com/nidhal-jabnouni/siem_llm_integration.git
cd siem_llm_integration
2. Set Up Virtual Environment
To keep this setup isolated, create and activate a virtual environment:

bash
Copier
Modifier
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
3. Install Required Packages
Install the required dependencies from the requirements.txt file:

bash
Copier
Modifier
pip install -r requirements.txt
4. Configure Environment Variables
Modify the .env file with your credentials and other configuration details. Ensure the following environment variables are set:


5. Perform Basic Operations
Once the environment is set up, you can perform the following operations:

Index Logs
Index your logs to the Chroma database:

bash
Copier
Modifier
python main.py index --log-file logs/fox_alerts.txt
Search Logs
Search the logs for specific terms like "suspicious DNS queries":

bash
Copier
Modifier
python main.py search "suspicious DNS queries"
Enrich Logs
Enrich logs with additional data for improved analysis:

bash
Copier
Modifier
python main.py enrich
6. Visualize Chroma Database Content
Once your data is indexed, you can visualize and interact with the Chroma vector database:

Cloning Chroma-Peek Repository
To visualize the contents of your Chroma database, clone the Chroma-Peek repository:

bash
Copier
Modifier
git clone https://github.com/Pawandeep-prog/chroma-peek.git
cd chroma-peek
Set Up Visualization Environment
Create and Activate a Virtual Environment

bash
Copier
Modifier
python -m venv chroma-visualize-env
chroma-visualize-env\Scripts\activate   # Windows
source chroma-visualize-env/bin/activate # macOS/Linux
Install Dependencies

Install the required dependencies from the requirements.txt file inside the chroma-peek folder:

bash
Copier
Modifier
pip install -r requirements.txt
Run Streamlit App

Start the visualization app using Streamlit:

bash
Copier
Modifier
streamlit run chroma-peek/main.py
Enter Chroma DB Path

When the Streamlit app launches in your browser, enter the path to your Chroma database. For example:

text
Copier
Modifier
C:\Users\ossam\OneDrive\Bureau\siem_llm_integration\chroma_logs_db
Press Enter to load the Chroma DB contents.

🔧 What You Can Do with Chroma Visualization
Once the Streamlit app is running and you’ve provided the Chroma DB path, you can:

View the indexed logs in a visual format.

Search for specific logs or terms.

Interact with the vector database for further insights into your SIEM data.
