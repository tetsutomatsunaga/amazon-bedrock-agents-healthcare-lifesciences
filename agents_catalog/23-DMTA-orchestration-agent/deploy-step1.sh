#!/bin/bash

echo "🚀 Step 1: Deploying DMTA Orchestration Agent (Basic Functions)"
echo "=============================================================="

export BEDROCK_AGENT_SERVICE_ROLE_ARN="arn:aws:iam::590183741681:role/BedrockAgentRole"
./deploy.sh

if [ $? -eq 0 ]; then
    echo "✅ Step 1 completed successfully!"
    echo "📋 Next steps:"
    echo "   2. Run ./setup-knowledge-base.sh to create Knowledge Base"
    echo "   3. Run ./deploy-step2.sh to link Knowledge Base to Agent"
else
    echo "❌ Step 1 failed. Please check the errors above."
    exit 1
fi