#!/bin/bash

echo "📚 Step 2: Setting up Knowledge Base"
echo "===================================="

# Create S3 bucket for Knowledge Base
BUCKET_NAME="dmta-kb-$(date +%s)-$(shuf -i 1000-9999 -n 1)"
echo "Creating S3 bucket: $BUCKET_NAME"

aws s3 mb s3://$BUCKET_NAME --region us-west-2

if [ $? -eq 0 ]; then
    echo "✅ S3 bucket created: $BUCKET_NAME"
    
    # Upload knowledge base data
    echo "📤 Uploading knowledge base data..."
    aws s3 cp knowledge-base/project-001.md s3://$BUCKET_NAME/projects/project-001.md
    aws s3 cp knowledge-base/project-015.md s3://$BUCKET_NAME/projects/project-015.md
    aws s3 cp knowledge-base/project-087.md s3://$BUCKET_NAME/projects/project-087.md
    
    echo "✅ Knowledge base data uploaded!"
    echo "📋 Files in bucket:"
    aws s3 ls s3://$BUCKET_NAME/projects/ --recursive
    
    # Save bucket name for next step
    echo $BUCKET_NAME > .kb-bucket-name
    
    echo "🔧 Creating Knowledge Base automatically..."
    
    # Create Knowledge Base using AWS CLI
    KB_NAME="DMTA-Knowledge-Base-$(date +%s)"
    
    # Note: Knowledge Base creation via CLI requires complex setup
    # For now, providing the CLI commands for manual execution
    echo ""
    echo "📋 Run these commands to create Knowledge Base:"
    echo ""
    echo "# 1. Create Knowledge Base"
    echo "aws bedrock-agent create-knowledge-base \\"
    echo "  --name '$KB_NAME' \\"
    echo "  --description 'DMTA project knowledge base' \\"
    echo "  --role-arn 'arn:aws:iam::590183741681:role/BedrockAgentRole' \\"
    echo "  --knowledge-base-configuration '{\"type\":\"VECTOR\",\"vectorKnowledgeBaseConfiguration\":{\"embeddingModelArn\":\"arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v1\"}}' \\"
    echo "  --storage-configuration '{\"type\":\"OPENSEARCH_SERVERLESS\"}' \\"
    echo "  --region us-west-2"
    echo ""
    echo "# 2. Create Data Source"
    echo "aws bedrock-agent create-data-source \\"
    echo "  --knowledge-base-id <KB_ID_FROM_STEP1> \\"
    echo "  --name 'dmta-projects' \\"
    echo "  --data-source-configuration '{\"type\":\"S3\",\"s3Configuration\":{\"bucketArn\":\"arn:aws:s3:::$BUCKET_NAME\",\"inclusionPrefixes\":[\"projects/\"]}}' \\"
    echo "  --region us-west-2"
    echo ""
    echo "📝 Bucket name saved to .kb-bucket-name"
    echo "💡 After creating KB, run: ./deploy-step3.sh <KNOWLEDGE_BASE_ID>"
    
else
    echo "❌ Failed to create S3 bucket"
    exit 1
fi