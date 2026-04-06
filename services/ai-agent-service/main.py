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
from fastapi import FastAPI
import uvicorn

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
except Exception:
    try:
        config.load_kube_config()
    except Exception:
        logger.warning("Kubernetes config not loaded - remediation disabled")

k8s_apps = client.AppsV1Api()
anthropic_client = Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None

SEVERITY_EMOJI = {
    "low": "\U0001f7e1",
    "medium": "\U0001f7e0",
    "high": "\U0001f534",
    "critical": "\U0001f6a8"
}


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


def send_slack_notification(message):
    if not SLACK_WEBHOOK:
        logger.info(f"Slack (simulated): {message}")
        return
    try:
        requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=5)
        logger.info("Slack notification sent")
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")


def build_slack_message(anomaly, ai_response, remediation_result):
    severity = ai_response.get("severity", "medium")
    emoji = SEVERITY_EMOJI.get(severity, "\U0001f534")
    steps = ai_response.get("remediation_steps", [])
    steps_text = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(steps)])
    return (
        f"{emoji} *PulseShield AI Incident Alert*\n"
        f"{'='*40}\n"
        f"*Severity:* {severity.upper()}\n"
        f"*Service:* {anomaly['service']}\n"
        f"*Issue Type:* {anomaly['type']}\n"
        f"*Metric Value:* {anomaly['value']} (threshold: {anomaly['threshold']})\n\n"
        f"*Summary:* {ai_response.get('summary', 'N/A')}\n\n"
        f"*Root Cause:* {ai_response.get('root_cause', 'N/A')}\n\n"
        f"*Impact:* {ai_response.get('impact', 'N/A')}\n\n"
        f"*AI Analysis:* {ai_response.get('reasoning', 'N/A')}\n\n"
        f"*Remediation Steps:*\n{steps_text}\n\n"
        f"*Action Taken:* {remediation_result}\n"
        f"*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )


def analyze_with_ai(anomaly, metrics_snapshot):
    if not anthropic_client:
        return {
            "action": "alert",
            "severity": "medium",
            "summary": "AI not configured",
            "root_cause": "N/A",
            "impact": "N/A",
            "reasoning": "AI not configured",
            "remediation_steps": ["Check AI agent configuration"]
        }

    prompt = f"""You are a senior DevOps AI agent monitoring a Kubernetes microservices platform called PulseShield AI.

An anomaly has been detected. Analyze it thoroughly and respond with a detailed incident report.

Anomaly Details:
{json.dumps(anomaly, indent=2)}

Metrics Snapshot:
{json.dumps(metrics_snapshot, indent=2)}

Provide your response as JSON only with this exact structure:
{{
  "action": "restart|scale|alert",
  "severity": "low|medium|high|critical",
  "summary": "one sentence summary of the issue",
  "root_cause": "likely root cause of the anomaly",
  "impact": "what is the impact on users and the system",
  "reasoning": "detailed explanation of your analysis",
  "remediation_steps": ["step 1", "step 2", "step 3"],
  "scale_replicas": 3
}}"""

    try:
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {
            "action": "alert",
            "severity": "high",
            "summary": f"Anomaly detected on {anomaly.get('service', 'unknown')}",
            "root_cause": f"Metric value {anomaly.get('value')} exceeded threshold {anomaly.get('threshold')}",
            "impact": "Service degradation detected. Users may experience errors or slow responses.",
            "reasoning": f"Automated detection triggered. AI analysis unavailable: {str(e)}",
            "remediation_steps": [
                f"Check logs: kubectl logs -l app={anomaly.get('service')} -n pulseshield",
                f"Check pods: kubectl get pods -n pulseshield",
                f"Restart: kubectl rollout restart deployment/{anomaly.get('service')} -n pulseshield",
                "Monitor metrics in Grafana dashboard",
                "Escalate to on-call engineer if issue persists"
            ]
        }


def execute_remediation(action, service, namespace="pulseshield"):
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


def detect_anomalies():
    anomalies = []

    error_rate = query_prometheus('rate(http_requests_total{status=~"4..|5.."}[5m])')
    if error_rate and error_rate.get('data', {}).get('result'):
        for result in error_rate['data']['result']:
            value = float(result['value'][1])
            if value > 0.01:
                anomalies.append({
                    "type": "high_error_rate",
                    "service": result['metric'].get('app', result['metric'].get('job', 'unknown')),
                    "value": round(value, 4),
                    "threshold": 0.01
                })

    latency = query_prometheus('histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))')
    if latency and latency.get('data', {}).get('result'):
        for result in latency['data']['result']:
            value = float(result['value'][1])
            if value > 1.0:
                anomalies.append({
                    "type": "high_latency",
                    "service": result['metric'].get('app', result['metric'].get('job', 'unknown')),
                    "value": round(value, 4),
                    "threshold": 1.0
                })

    restarts = query_prometheus('increase(kube_pod_container_status_restarts_total{namespace="pulseshield"}[10m])')
    if restarts and restarts.get('data', {}).get('result'):
        for result in restarts['data']['result']:
            value = float(result['value'][1])
            if value > 1:
                anomalies.append({
                    "type": "pod_restarts",
                    "service": result['metric'].get('pod', 'unknown'),
                    "value": round(value, 2),
                    "threshold": 1
                })

    return anomalies


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
                    message = build_slack_message(anomaly, ai_response, remediation_result)
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
            else:
                logger.info("No anomalies detected")
            time.sleep(60)
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            time.sleep(60)


app = FastAPI(title="AI Agent Service")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-agent-service"}


@app.post("/trigger-alert")
async def trigger_alert():
    anomaly = {"type": "manual_test", "service": "order-service", "value": 0.99, "threshold": 0.01}
    ai_response = analyze_with_ai(anomaly, {})
    action = ai_response.get("action", "alert")
    remediation_result = execute_remediation(action, anomaly['service'])
    message = build_slack_message(anomaly, ai_response, remediation_result)
    send_slack_notification(message)
    return {"status": "alert sent", "severity": ai_response.get("severity"), "action": action}


if __name__ == "__main__":
    init_db()
    monitoring_thread = Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
