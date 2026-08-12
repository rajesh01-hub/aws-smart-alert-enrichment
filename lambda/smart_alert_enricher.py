import boto3
import json
import time
import os

logs_client = boto3.client('logs')
sns_client = boto3.client('sns')

LOG_GROUP = os.environ.get('LOG_GROUP', '/aws/app/log-monitoring-demo')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:ap-south-1:629720698520:app-critical-alerts-topic')

def lambda_handler(event, context):
    query = "fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 5"
    
    start_time = int(time.time()) - 300  # Last 5 minutes
    end_time = int(time.time())
    
    start_query_response = logs_client.start_query(
        logGroupName=LOG_GROUP,
        startTime=start_time,
        endTime=end_time,
        queryString=query
    )
    
    query_id = start_query_response['queryId']
    
    response = None
    while response is None or response['status'] in ['Running', 'Scheduled']:
        time.sleep(1)
        response = logs_client.get_query_results(queryId=query_id)
        
    results = response.get('results', [])
    
    context_lines = []
    if not results:
        context_lines.append("Alarm triggered, but no specific error traces were found in the last 5 minutes.")
    else:
        for idx, row in enumerate(results, 1):
            msg = [field['value'] for field in row if field['field'] == '@message'][0]
            ts = [field['value'] for field in row if field['field'] == '@timestamp'][0]
            context_lines.append(f"--- Error Trace #{idx} [@ {ts}] ---\n{msg}\n")
            
    enriched_body = f"""🚨 PRODUCTION INCIDENT ALERT 🚨

Target Log Group: {LOG_GROUP}
Trigger Window: Last 5 Minutes
Status: CRITICAL

==========================================
RECENT LOG CONTEXT (ENRICHED BY LAMBDA)
==========================================
{'\n'.join(context_lines)}

==========================================
RECOMMENDED ACTION ITEMS
==========================================
1. Review the stack trace above for null pointers or failed connections.
2. Verify recent code deployments or environment changes.
3. Check status of downstream database dependencies.
"""

    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="🚨 [CRITICAL] Production Incident Alert: Log Errors Detected",
        Message=enriched_body
    )
    
    return {"statusCode": 200, "body": "Alert enriched and published successfully"}
