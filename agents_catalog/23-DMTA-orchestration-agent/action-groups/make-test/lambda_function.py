import json
import boto3
import os
import random
import statistics
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """Handle make_test function - Execute expression and SPR binding assays with FactorX simulation"""
    print(f"Received event: {json.dumps(event)}")
    
    # Extract parameters from the event
    parameters = event.get('parameters', [])
    param_dict = {param['name']: param['value'] for param in parameters}
    
    variant_list = param_dict.get('variant_list', '[]')
    assay_type = param_dict.get('assay_type', 'SPR binding assay')
    target_protein = param_dict.get('target_protein', 'vWF A1 domain')
    quality_controls = param_dict.get('quality_controls', '{}')
    
    # Parse variant list and QC parameters
    if isinstance(variant_list, str):
        try:
            variant_list = json.loads(variant_list)
        except:
            variant_list = []
    
    try:
        qc_params = json.loads(quality_controls) if quality_controls else {}
    except:
        qc_params = {}
    
    # Generate FactorX experimental data
    results = generate_factorx_data(variant_list, assay_type, target_protein, qc_params)
    
    # Store results in DynamoDB and S3
    experiment_id = store_experimental_data(results, assay_type)
    
    # Generate assay report
    assay_report = generate_assay_report(results, assay_type, target_protein)
    
    # Convert Decimal to float for JSON serialization
    results_json = convert_decimals_to_float(results)
    assay_report_json = convert_decimals_to_float(assay_report)
    
    response_body = {
        'message': f'Completed {assay_type} for {len(results)} variants against {target_protein}',
        'experiment_id': experiment_id,
        'experimental_results': results_json,
        'assay_report': assay_report_json,
        'next_steps': 'Ready to start Analyze phase - update GP model and plan next cycle'
    }
    
    return {
        'response': {
            'actionGroup': event['actionGroup'],
            'function': event['function'],
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(response_body)
                    }
                }
            }
        }
    }

def generate_factorx_data(variant_list, assay_type, target_protein, qc_params):
    """Generate realistic FactorX dummy data for expression and SPR binding assays"""
    results = []
    num_variants = len(variant_list) if variant_list else 8
    
    for i in range(num_variants):
        variant_id = variant_list[i].get('variant_id', f'VAR_01_{i+1:02d}') if variant_list else f'VAR_01_{i+1:02d}'
        
        # Expression phase simulation
        base_yield = 60 + random.gauss(0, 15)
        expression_yield = max(10, base_yield + (i * 5))  # Some variants express better
        
        # SPR binding simulation with realistic kinetics
        ka_base = 1.5e5 + random.gauss(0, 2e4)
        kd_base = 3e-4 + random.gauss(0, 5e-5)
        
        # Calculate KD from kinetics
        binding_kd_nm = (kd_base / ka_base) * 1e9
        binding_kd_nm = max(0.1, binding_kd_nm - (i * 0.2))  # Progressive improvement
        
        # Quality assessment
        quality_factors = {
            'expression_quality': 1.0 if expression_yield > 30 else 0.7,
            'binding_specificity': 0.9 + random.gauss(0, 0.05),
            'stability_score': 0.85 + random.gauss(0, 0.1)
        }
        quality_score = statistics.mean(list(quality_factors.values()))
        
        result = {
            'variant_id': variant_id,
            'expression_data': {
                'yield_mg_per_l': Decimal(str(round(expression_yield, 1))),
                'purity_percent': Decimal(str(round(85 + random.gauss(0, 5), 1))),
                'aggregation_percent': Decimal(str(round(max(0, 5 + random.gauss(0, 2)), 1)))
            },
            'spr_binding_data': {
                'binding_kd_nm': Decimal(str(round(binding_kd_nm, 2))),
                'kinetics': {
                    'ka_per_m_per_s': Decimal(str(round(ka_base, 0))),
                    'kd_per_s': Decimal(str(round(kd_base, 6))),
                    'rmax_ru': Decimal(str(round(150 + random.gauss(0, 30), 1)))
                },
                'binding_response': generate_spr_curve(ka_base, kd_base)
            },
            'quality_assessment': {
                'overall_score': Decimal(str(round(quality_score, 2))),
                'factors': {
                    'expression_quality': Decimal(str(quality_factors['expression_quality'])),
                    'binding_specificity': Decimal(str(quality_factors['binding_specificity'])),
                    'stability_score': Decimal(str(quality_factors['stability_score']))
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        results.append(result)
    
    return results

def generate_spr_curve(ka, kd):
    """Generate realistic SPR binding curve data"""
    concentrations = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0]  # nM
    responses = []
    
    for conc in concentrations:
        # Steady-state binding response
        conc_m = conc * 1e-9
        response = (150 * conc_m) / (kd/ka + conc_m)  # Langmuir binding
        response += random.gauss(0, response * 0.05)  # Add noise
        responses.append(round(max(0, response), 1))
    
    return {
        'concentrations_nm': concentrations,
        'responses_ru': responses,
        'r_squared': round(0.95 + random.gauss(0, 0.03), 3)
    }

def store_experimental_data(results, assay_type):
    """Store experimental results in DynamoDB and S3"""
    experiment_id = f'EXP_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    try:
        # Store summary in DynamoDB
        # Get the latest project_id from ProjectTable
        project_table = dynamodb.Table(os.environ.get('PROJECT_TABLE', 'DMTAProjectTable'))
        project_response = project_table.scan()
        if project_response['Items']:
            latest_project = max(project_response['Items'], key=lambda x: x['created_at'])
            project_id = latest_project['project_id']
        else:
            project_id = 'default-project'
            
        table = dynamodb.Table(os.environ.get('VARIANT_TABLE', 'DMTAVariantTable'))
        for result in results:
            result['project_id'] = project_id
            result['experiment_id'] = experiment_id
            result['assay_type'] = assay_type
            # Store in DynamoDB (simplified for demo)
            
        # Store detailed data in S3 under project
        project_id = os.environ.get('PROJECT_ID', 'default-project')
        s3_key = f'projects/{project_id}/experiments/{experiment_id}/results.json'
        results_json = convert_decimals_to_float(results)
        s3.put_object(
            Bucket=os.environ.get('S3_BUCKET', 'dmta-data'),
            Key=s3_key,
            Body=json.dumps(results_json, indent=2)
        )
        print(f"Stored experimental data: {experiment_id}")
        
    except Exception as e:
        print(f"Error storing data: {str(e)}")
    
    return experiment_id

def generate_assay_report(results, assay_type, target_protein):
    """Generate comprehensive assay report"""
    # Calculate summary statistics
    kd_values = [r['spr_binding_data']['binding_kd_nm'] for r in results]
    expression_yields = [r['expression_data']['yield_mg_per_l'] for r in results]
    
    report = {
        'assay_summary': {
            'assay_type': assay_type,
            'target_protein': target_protein,
            'variants_tested': len(results),
            'success_rate': len([r for r in results if r['expression_data']['yield_mg_per_l'] > 20]) / len(results)
        },
        'binding_statistics': {
            'best_kd_nm': round(min(kd_values), 2),
            'median_kd_nm': round(statistics.median(kd_values), 2),
            'kd_range': [round(min(kd_values), 2), round(max(kd_values), 2)]
        },
        'expression_statistics': {
            'mean_yield': round(statistics.mean(expression_yields), 1),
            'yield_range': [round(min(expression_yields), 1), round(max(expression_yields), 1)]
        },
        'assay_conditions': {
            'temperature': '25°C',
            'buffer': 'HBS-EP+ (10mM HEPES, 150mM NaCl, 3mM EDTA, 0.05% P20)',
            'flow_rate': '30 μL/min',
            'contact_time': '120 seconds',
            'dissociation_time': '300 seconds'
        }
    }
    
    return report

def convert_decimals_to_float(obj):
    """Recursively convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj