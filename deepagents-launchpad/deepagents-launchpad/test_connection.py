import os
import sys
import boto3

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from supervisor import load_aws_credentials

load_aws_credentials()

print("Checking environment variables...")
print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION')}")
key_id = os.getenv("AWS_ACCESS_KEY_ID") or ""
print(f"AWS_ACCESS_KEY_ID: {key_id[:8]}... (hidden for safety)" if key_id else "AWS_ACCESS_KEY_ID: missing")

try:
    # 2. Establish connection to Bedrock in Singapore
    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )
    
    # 3. Test a fast, cheap call using Claude 3 Haiku
    print("\nSending test message to Amazon Bedrock...")
    response = bedrock.converse(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        messages=[
            {
                "role": "user",
                "content": [{"text": "Say 'System Connection Successful' in 5 words or less."}]
            }
        ],
        inferenceConfig={"maxTokens": 20}
    )
    
    # 4. Print the model's response
    reply = response["output"]["message"]["content"][0]["text"]
    print(f"\n✅ Connection Successful!")
    print(f"Bedrock Response: '{reply}'")

except Exception as e:
    print("\nConnection Failed!")
    print("Please check that your temporary credentials in your .env file have not expired.")
    print("Error Details:")
    print(str(e))