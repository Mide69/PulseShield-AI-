import os
import json
import time
import logging
import requests
from datetime import datetime
from anthropic import Anthropic
from kubernetes import client, config
import psycopg2
from threading import Thread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "incidents"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

try:
    config.load_incluster_config()
except:
    try:
        config.load_kube_config()
    except:
        logger.warning("Kubernetes config not loaded - remediation disabled")

k8s_apps = client.AppsV1Api()
k8s_core = client.CoreV1Api()
anthropic_client = Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None

def init_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                service VARCHAR(255),
                anomaly_type VARCHAR(255),
                metrics_snapshot TEXT,
                ai_diagnosis TEXT,
                remediation_action VARCHAR(255),
                status VARCHAR(50),
                slack_sent BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"DB init failed: {e}")

def query_prometheus(query):
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query}, timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Prometheus query failed: {e}")
        return None

def detect_anomalies():
    anomalies = []
    
    error_rate = query_prometheus('rate(http_requests_total{status=~"5.."}[5m])')
    if error_rate and error_rate.get('data', {}).get('result'):
        for result in error_rate['data']['result']:
            value = float(result['value'][1])
            if value > 0.05:
                anomalies.append({
                    "type": "high_error_rate",
                    "service": result['metric'].get('job', 'unknown'),
                    "value": value,
                    "threshold": 0.05
                })
    
    latency = query_prometheus('histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))')
    if latency and latency.get('data', {}).get('result'):
        for result in latency['data']['result']:
            value = float(result['value'][1])
            if value > 2.0:
                anomalies.append({
                    "type": "high_latency",
                    "service": result['metric'].get('job', 'unknown'),
                    "value": value,
                    "threshold": 2.0
                })
    
    restarts = query_prometheus('increase(kube_pod_container_status_restarts_total[10m])')
    if restarts and restarts.get('data', {}).get('result'):
        for result in restarts['data']['result']:
            value = float(result['value'][1])
            if value > 3:
                anomalies.append({
                    "type": "pod_restarts",
                    "service": result['metric'].get('pod', 'unknown'),
                    "value": value,
                    "threshold": 3
                })
    
    return anomalies

def analyze_with_ai(anomaly, metrics_snapshot):
    if not anthropic_client:
        return {"action": "alert", "reasoning": "AI not configured"}
    
    prompt = f"""You are a DevOps AI agent. Analyze this anomaly and recommend remediation.

Anomaly: {json.dumps(anomaly, indent=2)}
Metrics: {json.dumps(metrics_snapshot, indent=2)}

Respond with JSON only:
{{
  "action": "restart|scale|alert",
  "reasoning": "brief explanation",
  "scale_replicas": 3
}}"""

    try:
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {"action": "alert", "reasoning": str(e)}

def execute_remediation(action, service, namespace="default"):
    try:
        if action == "restart":
            k8s_apps.patch_namespaced_deployment(
                name=service,
                namespace=namespace,
                body={"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": datetime.now().isoformat()}}}}}
            )
            logger.info(f"Restarted deployment: {service}")
            return "restarted"
        
        elif action == "scale":
            deployment = k8s_apps.read_namespaced_deployment(service, namespace)
            current_replicas = deployment.spec.replicas
            new_replicas = current_replicas + 2
            k8s_apps.patch_namespaced_deployment_scale(
                name=service,
                namespace=namespace,
                body={"spec": {"replicas": new_replicas}}
            )
            logger.info(f"Scaled {service} from {current_replicas} to {new_replicas}")
            return f"scaled to {new_replicas}"
        
        return "alert_only"
    except Exception as e:
        logger.error(f"Remediation failed: {e}")
        return f"failed: {e}"

def send_slack_notification(message):
    if not SLACK_WEBHOOK:
        logger.info(f"Slack (simulated): {message}")
        return
    
    try:
        requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=5)
        logger.info("Slack notification sent")
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")

def log_incident(incident_data):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidents (service, anomaly_type, metrics_snapshot, ai_diagnosis, remediation_action, status, slack_sent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            incident_data['service'],
            incident_data['anomaly_type'],
            json.dumps(incident_data['metrics']),
            incident_data['ai_diagnosis'],
            incident_data['action'],
            incident_data['status'],
            incident_data['slack_sent']
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log incident: {e}")

def monitoring_loop():
    logger.info("AI Agent monitoring started")
    
    while True:
        try:
            anomalies = detect_anomalies()
            
            if anomalies:
                logger.info(f"Detected {len(anomalies)} anomalies")
                
                for anomaly in anomalies:
                    metrics_snapshot = query_prometheus(f'{{job="{anomaly["service"]}"}}')
                    ai_response = analyze_with_ai(anomaly, metrics_snapshot)
                    
                    action = ai_response.get("action", "alert")
                    reasoning = ai_response.get("reasoning", "No reasoning provided")
                    
                    remediation_result = execute_remediation(action, anomaly['service'])
                    
                    message = f"🚨 *PulseShield Alert*\n" \
                              f"Service: {anomaly['service']}\n" \
                              f"Issue: {anomaly['type']}\n" \
                              f"Value: {anomaly['value']}\n" \
                              f"AI Recommendation: {action}\n" \
                              f"Reasoning: {reasoning}\n" \
                              f"Action Taken: {remediation_result}"
                    
                    send_slack_notification(message)
                    
                    log_incident({
                        'service': anomaly['service'],
                        'anomaly_type': anomaly['type'],
                        'metrics': anomaly,
                        'ai_diagnosis': reasoning,
                        'action': remediation_result,
                        'status': 'resolved' if action != 'alert' else 'alerted',
                        'slack_sent': True
                    })
            
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    init_db()
    monitoring_thread = Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title="AI Agent Service")
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "ai-agent-service"}
    
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
