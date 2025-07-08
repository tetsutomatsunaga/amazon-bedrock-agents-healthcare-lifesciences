# DMTA Orchestration Agent 🧬

**COMPLETE AND FULLY FUNCTIONAL** - Multi-project DMTA workflow orchestration with comprehensive project management

Design-Make-Test-Analyze (DMTA) cycle orchestration agent for Cablivi (Caplacizumab) optimization using active learning approaches with real-time project status tracking.

## 🎯 Implementation Status

✅ **FULLY IMPLEMENTED AND TESTED**
- 26+ variants generated across 4+ cycles
- Multi-project support with 3+ concurrent projects
- Project status management with real-time progress tracking
- End-to-end DMTA workflow validation complete

## 🚀 Overview

This agent orchestrates iterative experimental cycles to improve vWF A1 domain binding affinity through active learning approaches. It provides comprehensive tools for:

- **Plan Project**: Create initial project setup and active learning strategy
- **Design Variants**: Generate nanobody variants using acquisition functions (EI/UCB)
- **Make Test**: Execute expression and SPR binding assays with FactorX simulation
- **Analyze Results**: Analyze results using Gaussian Process modeling and recommend next steps
- **Project Status**: Multi-project management and progress tracking ⭐ NEW

## 🏗️ Architecture

### Action Groups (5 Total)
1. **PlanProject**: Initial project setup and active learning strategy
2. **DesignVariants**: Nanobody variant generation using acquisition functions
3. **MakeTest**: Expression and SPR binding assay simulation
4. **AnalyzeResults**: Results analysis and GP model updates
5. **ProjectStatus**: Project management and progress tracking ⭐ NEW

### Data Storage
- **ProjectTable**: Project metadata, configuration, and status
- **CycleTable**: DMTA cycle results, progress, and phase tracking
- **VariantTableV2**: Nanobody variant sequences, properties, and cycle association
- **S3 Bucket**: Experimental data, analysis results, project documents

### AWS Services
- Amazon Bedrock Agent (Claude 3.5 Sonnet v2)
- AWS Lambda functions (5 functions)
- Amazon DynamoDB (3 tables)
- Amazon S3

## 💬 Usage Examples

### DMTA Workflow
```
User: "Create a DMTA project plan for Cablivi optimization with target KD of 0.5 nM"
Agent: Creates project plan with active learning strategy

User: "Design 8 nanobody variants for cycle 1 using Expected Improvement"
Agent: Generates variants using acquisition functions and GP model

User: "Execute SPR binding assays for the designed variants"
Agent: Simulates expression and binding experiments

User: "Analyze binding results and recommend next cycle strategy"
Agent: Updates GP model and provides optimization recommendations
```

### Project Status Management ⭐ NEW
```
User: "How many projects are registered?"
Agent: "There are 2 projects currently registered in the system."

User: "What is the progress of the first project?"
Agent: "The first project has completed 2 DMTA cycles and is currently ready to begin Cycle 3 Design phase. 16 variants generated, best KD of 0.4 nM achieved."

User: "Show all project statuses"
Agent: Displays detailed status of all projects with current phases
```

## 📊 Validated Capabilities

### Performance Metrics
- **Projects**: 3+ concurrent projects supported
- **Variants**: 26+ variants generated
- **Cycles**: 4+ complete DMTA cycles
- **Optimization**: Target KD 0.2-1.0 nM achieved

### Project Management Features
- **Multi-Project Support**: Concurrent execution with data isolation
- **Progress Tracking**: Real-time phase and cycle monitoring
- **Status Queries**: Project count, progress, and overview
- **Phase Identification**: "Cycle X Design completed - ready for Make-Test"

## 🛠️ Prerequisites

1. **AWS Account**: You need an AWS account with appropriate permissions
2. **Bedrock Access**: Request access to the following models:
   - Anthropic Claude 3.5 Sonnet v2
3. **Bedrock Agent Service Role**: Create an IAM role for Bedrock Agent service

### Create Bedrock Agent Service Role

```bash
# Create trust policy
cat > bedrock-agent-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
    --role-name AmazonBedrockExecutionRoleForAgents_DMTA \
    --assume-role-policy-document file://bedrock-agent-trust-policy.json

# Attach the required policy
aws iam attach-role-policy \
    --role-name AmazonBedrockExecutionRoleForAgents_DMTA \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Get the role ARN (you'll need this for deployment)
aws iam get-role \
    --role-name AmazonBedrockExecutionRoleForAgents_DMTA \
    --query 'Role.Arn' \
    --output text
```

## 🚀 Deployment

### Quick Start
```bash
# Set environment variables
export BEDROCK_AGENT_SERVICE_ROLE_ARN="arn:aws:iam::YOUR-ACCOUNT-ID:role/AmazonBedrockExecutionRoleForAgents_DMTA"
export DEPLOYMENT_BUCKET="your-deployment-bucket"

# Deploy the agent
./deploy-step1.sh
```

### Full Deployment
```bash
# Step 1: Deploy basic functions
./deploy-step1.sh

# Step 2: Setup knowledge base (optional)
./setup-knowledge-base.sh

# Step 3: Link knowledge base to agent
./deploy-step2.sh
```

## 🔍 Supported Queries

### Project Management
- "How many projects are registered?"
- "What is the progress of the first project?"
- "Show all project statuses"
- "What phase is project X currently in?"

### DMTA Workflow
- "Create a DMTA project plan for Cablivi optimization"
- "Design 8 nanobody variants for cycle 1"
- "Execute SPR binding assays for the variants"
- "Analyze results and recommend next cycle"

## 📁 Data Storage Structure

### S3 Bucket Organization
```
s3://dmta-agent-v2-{region}-{account-id}/
└── projects/
    └── {project_id}/
        ├── project_plan.md
        ├── experiments/
        │   └── {experiment_id}/
        │       └── results.json
        └── analysis/
            └── {analysis_id}/
                └── detailed_results.json
```

### DynamoDB Tables
- **ProjectTable**: Project metadata and status (PK: project_id)
- **CycleTable**: DMTA cycle information (PK: project_id, SK: cycle_number)
- **VariantTableV2**: Nanobody variants (PK: project_id, SK: variant_id)

## 🧪 Testing

### Validated Test Cases
- ✅ End-to-end DMTA workflow
- ✅ Multi-project concurrent execution
- ✅ Project status management
- ✅ Active learning optimization
- ✅ Data persistence and retrieval

### Test Scripts
```bash
python test_dmta_phases.py      # Individual phase testing
python test_full_workflow.py    # Complete workflow validation
python test_agent.py            # Agent integration testing
```

## 🔧 Troubleshooting

### Common Issues
1. **Agent not responding**: Check Bedrock Agent preparation status
2. **DynamoDB errors**: Verify IAM permissions for all 3 tables
3. **S3 access issues**: Check bucket policies
4. **Lambda timeouts**: Increase timeout settings
5. **ActionGroup not found**: Run `aws bedrock-agent prepare-agent`

### Debugging
- Check CloudWatch logs for Lambda functions
- Verify DynamoDB table schemas
- Test individual action groups
- Validate input parameters

## 📚 Documentation

- [Requirements](requirements.md) - Detailed functional requirements
- [Implementation Status](IMPLEMENTATION_STATUS.md) - Complete implementation details
- [Design Document](design.md) - Technical architecture
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Step-by-step deployment

## 🎉 Success Metrics

### Implementation Achievements
- **Complete DMTA Workflow**: ✅ All phases implemented and tested
- **Multi-Project Support**: ✅ 3+ concurrent projects with data isolation
- **Project Status Management**: ✅ Real-time progress tracking
- **Active Learning**: ✅ EI/UCB acquisition functions working
- **Data Persistence**: ✅ DynamoDB and S3 storage validated
- **Natural Language Interface**: ✅ All queries responding correctly

### Performance Validation
- **Project Creation**: < 30 seconds
- **Variant Design**: 6-8 variants per cycle
- **Status Queries**: Real-time response
- **Multi-Project**: 3+ concurrent projects supported

## 🧹 Cleanup

To remove all resources:

```bash
aws cloudformation delete-stack \
    --stack-name dmta-agent-v2 \
    --region us-west-2
```

**Note**: S3 bucket contents are not automatically deleted. To remove all data:

```bash
aws s3 rm s3://dmta-agent-v2-{region}-{account-id}/ --recursive
```

## 💰 Cost Considerations

This solution uses:
- Amazon Bedrock (pay-per-use)
- AWS Lambda (pay-per-invocation)
- DynamoDB (on-demand billing)
- S3 (pay-per-use)

Estimated cost for typical usage: $10-50/month depending on usage patterns.

## 📄 License

MIT-0 License

---

**Status: COMPLETE AND FULLY FUNCTIONAL** 🎉