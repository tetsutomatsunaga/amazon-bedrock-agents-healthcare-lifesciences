import json
import boto3
import os
import random
import traceback
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """Handle design_variants function"""
    print(f"Received event: {json.dumps(event)}")
    
    # Extract parameters from the event
    parameters = event.get('parameters', [])
    param_dict = {param['name']: param['value'] for param in parameters}
    
    parent_nanobody = param_dict.get('parent_nanobody', 'Cablivi')
    cycle_number = int(param_dict.get('cycle_number', 1))
    acquisition_function = param_dict.get('acquisition_function', 'Expected Improvement')
    num_variants = int(param_dict.get('num_variants', 8))
    previous_results = param_dict.get('previous_results', '{}')
    
    # Parse previous results for GP model
    try:
        prev_data = json.loads(previous_results) if previous_results else {}
    except:
        prev_data = {}
    
    # Update Gaussian Process model with previous results
    gp_model = update_gp_model(prev_data, cycle_number)
    
    # Generate variants using acquisition function
    variants = generate_variants_with_acquisition(
        parent_nanobody, cycle_number, acquisition_function, 
        num_variants, gp_model
    )
    
    # Store variants in DynamoDB
    try:
        # Get the latest project_id from ProjectTable
        project_table_name = os.environ.get('PROJECT_TABLE', 'DMTAProjectTable')
        variant_table_name = os.environ.get('VARIANT_TABLE', 'DMTAVariantTable')
        print(f"Using PROJECT_TABLE: {project_table_name}")
        print(f"Using VARIANT_TABLE: {variant_table_name}")
        
        project_table = dynamodb.Table(project_table_name)
        project_response = project_table.scan()
        print(f"Found {len(project_response['Items'])} projects")
        
        if project_response['Items']:
            # Get the most recent project
            latest_project = max(project_response['Items'], key=lambda x: x['created_at'])
            project_id = latest_project['project_id']
            print(f"Using project_id: {project_id}")
        else:
            project_id = 'default-project'
            print(f"No projects found, using default: {project_id}")
        
        table = dynamodb.Table(variant_table_name)
        for i, variant in enumerate(variants):
            variant['project_id'] = project_id
            variant['created_at'] = datetime.now().isoformat()
            variant['cycle_number'] = cycle_number
            table.put_item(Item=variant)
            print(f"Stored variant {i+1}: {variant['variant_id']}")
        print(f"Successfully stored {len(variants)} variants in DynamoDB")
    except Exception as e:
        print(f"Error storing variants: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    # Convert Decimal to float for JSON serialization
    variants_json = []
    for variant in variants:
        variant_json = variant.copy()
        variant_json['predicted_affinity'] = float(variant['predicted_affinity'])
        variant_json['acquisition_score'] = float(variant['acquisition_score'])
        variants_json.append(variant_json)
    
    gp_model_json = gp_model.copy()
    gp_model_json['model_accuracy'] = float(gp_model['model_accuracy'])
    gp_model_json['uncertainty_estimate'] = float(gp_model['uncertainty_estimate'])
    gp_model_json['hyperparameters'] = {
        'length_scale': float(gp_model['hyperparameters']['length_scale']),
        'signal_variance': float(gp_model['hyperparameters']['signal_variance']),
        'noise_variance': float(gp_model['hyperparameters']['noise_variance'])
    }
    
    response_body = {
        'message': f'Generated {num_variants} nanobody variants for cycle {cycle_number} using {acquisition_function}',
        'variants': variants_json,
        'acquisition_function': acquisition_function,
        'gp_model_stats': gp_model_json,
        'next_steps': 'Ready to start Make-Test phase - express and assay variants'
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

def update_gp_model(previous_data, cycle_number):
    """Update Gaussian Process model with previous experimental results"""
    # Mock GP model update
    model_stats = {
        'cycle': cycle_number,
        'training_points': len(previous_data.get('results', [])),
        'model_accuracy': Decimal(str(0.85 + (cycle_number * 0.02))),
        'uncertainty_estimate': Decimal(str(max(0.1, 0.3 - (cycle_number * 0.05)))),
        'hyperparameters': {
            'length_scale': Decimal('1.2'),
            'signal_variance': Decimal('0.8'),
            'noise_variance': Decimal('0.1')
        }
    }
    return model_stats

def generate_variants_with_acquisition(parent_nanobody, cycle_number, acquisition_function, num_variants, gp_model):
    """Generate nanobody variants using acquisition functions"""
    variants = []
    
    # Define mutation positions and options
    mutation_positions = [48, 50, 52, 99, 101, 103]  # CDR regions
    amino_acids = ['A', 'V', 'L', 'I', 'F', 'Y', 'W', 'S', 'T', 'N', 'Q']
    
    for i in range(num_variants):
        # Generate mutations
        mutations = []
        selected_positions = random.sample(mutation_positions, 2)
        for pos in selected_positions:
            original = 'A' if pos < 60 else 'S'
            available_aa = [aa for aa in amino_acids if aa != original]
            new_aa = random.choice(available_aa)
            mutations.append(f'{original}{pos}{new_aa}')
        
        # Calculate acquisition score based on function type
        if acquisition_function == 'Expected Improvement':
            acquisition_score = calculate_ei_score(i, gp_model)
        else:  # UCB
            acquisition_score = calculate_ucb_score(i, gp_model)
        
        variant = {
            'variant_id': f'VAR_{cycle_number}_{i+1:02d}',
            'sequence': f'QVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSGGSTYYADSVKGRFTISRDNSKNTLYLQMNSLRAEDTAVYYCAKVSYLSTASSLDYWGQGTLVTVSS_C{cycle_number}V{i+1}',
            'mutations': mutations,
            'predicted_affinity': Decimal(str(round(2.5 - (i * 0.15) + random.gauss(0, 0.1), 2))),
            'acquisition_score': Decimal(str(round(acquisition_score, 3))),
            'acquisition_function': acquisition_function
        }
        variants.append(variant)
    
    # Sort by acquisition score (descending)
    variants.sort(key=lambda x: x['acquisition_score'], reverse=True)
    return variants

def calculate_ei_score(variant_index, gp_model):
    """Calculate Expected Improvement score"""
    base_score = 0.9 - (variant_index * 0.08)
    uncertainty_bonus = float(gp_model['uncertainty_estimate']) * 0.3
    return max(0.1, base_score + uncertainty_bonus + random.gauss(0, 0.05))

def calculate_ucb_score(variant_index, gp_model):
    """Calculate Upper Confidence Bound score"""
    mean_prediction = 0.8 - (variant_index * 0.06)
    confidence_interval = float(gp_model['uncertainty_estimate']) * 1.96
    return max(0.1, mean_prediction + confidence_interval + random.gauss(0, 0.03))