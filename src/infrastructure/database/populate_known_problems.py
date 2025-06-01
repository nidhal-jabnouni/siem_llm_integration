from chromadb import PersistentClient
from src.infrastructure.embeddings.embedder import AzureEmbeddingFunction
import os
from dotenv import load_dotenv

load_dotenv()

def populate_db():
    db_path = "./chroma_known_problems_db"
    os.makedirs(db_path, exist_ok=True)
    client = PersistentClient(path=db_path)
    embedding_func = AzureEmbeddingFunction()

    try:
        collection = client.get_collection(name="known_problems")
        print("Collection 'known_problems' already exists. Clearing existing data...")
        client.delete_collection("known_problems")
    except Exception:
        print("Creating new collection 'known_problems'...")

    collection = client.create_collection(
        name="known_problems",
        embedding_function=embedding_func
    )

    samples = [
        ("DOS attack detected from IP 10.0.0.1",
         "Block the IP address using firewall rules and monitor for additional attacks"),
        ("Malware infection on host server1",
         "Isolate host from network, run comprehensive malware scan, and restore from clean backup"),
        ("Unauthorized access attempt detected",
         "Disable compromised user account immediately and force password reset"),
        ("SQL injection attack on web application",
         "Sanitize input parameters and update WAF rules to block similar patterns"),
        ("Brute force login attempts from multiple IPs", "Implement rate limiting and temporarily block source IPs"),
        ("Suspicious file upload detected", "Quarantine uploaded file and scan for malicious content"),
        ("Port scan detected from external IP", "Block scanning IP and alert network security team"),
        ("Privilege escalation attempt detected", "Review user permissions and disable affected account"),
        ("Data exfiltration detected on network", "Block outbound connections and investigate data access logs"),
        ("Phishing email detected in system", "Remove email from all inboxes and update email security filters"),
        ("Ransomware signature detected", "Immediately isolate affected systems and initiate incident response"),
        ("Certificate expired on web server", "Renew SSL certificate and update server configuration"),
        ("Weak password policy violation", "Enforce stronger password requirements and notify user"),
        ("Failed backup process detected", "Check backup system integrity and retry backup process"),
        ("Suspicious API usage patterns", "Review API access logs and implement additional authentication")
    ]

    documents = [issue for issue, _ in samples]
    metadatas = [{"fix": fix, "category": "security_incident"} for _, fix in samples]
    ids = [f"known_problem_{i}" for i in range(len(samples))]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Successfully populated database with {len(samples)} known problems")
    print(f"Database location: {db_path}")

    # Verify with query_texts
    query_text = "malware detection"
    test_query = collection.query(
        query_texts=[query_text],
        n_results=2
    )

    print("\nVerification - Sample query results:")
    for i, (doc, metadata) in enumerate(zip(test_query['documents'][0], test_query['metadatas'][0])):
        print(f"  {i + 1}. Problem: {doc}")
        print(f"     Fix: {metadata['fix']}")

def verify_db():
    db_path = "./chroma_known_problems_db"
    if not os.path.exists(db_path):
        print("❌ Database directory not found!")
        return False
    try:
        client = PersistentClient(path=db_path)
        collection = client.get_collection(name="known_problems")
        count = collection.count()
        print(f"✅ Database verified! Contains {count} documents")
        return True
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Initializing Known Problems Database...")
    populate_db()
    print("\nVerifying database...")
    verify_db()

