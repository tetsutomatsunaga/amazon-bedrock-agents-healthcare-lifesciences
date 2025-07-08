import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """Handle project_status function"""
    print(f"Received event: {json.dumps(event)}")
    
    parameters = event.get('parameters', [])
    param_dict = {param['name']: param['value'] for param in parameters}
    
    query_type = param_dict.get('query_type', 'all_projects')
    project_id = param_dict.get('project_id', '')
    
    try:
        if query_type == 'project_count':
            result = get_project_count()
        elif query_type == 'project_progress':
            result = get_project_progress(project_id)
        else:
            result = get_all_projects_status()
    except Exception as e:
        result = {'error': str(e)}
    
    return {
        'response': {
            'actionGroup': event['actionGroup'],
            'function': event['function'],
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({
                            'message': 'Project status retrieved',
                            'status_data': result
                        })
                    }
                }
            }
        }
    }

def get_project_count():
    """Get total number of projects"""
    project_table = dynamodb.Table(os.environ.get('PROJECT_TABLE'))
    response = project_table.scan()
    return {
        'total_projects': len(response['Items']),
        'projects': [{
            'project_id': item['project_id'],
            'target_kd_nm': float(item.get('target_kd_nm', 0)),
            'created_at': item.get('created_at')
        } for item in response['Items']]
    }

def get_project_progress(project_id):
    """Get project progress"""
    if not project_id:
        project_table = dynamodb.Table(os.environ.get('PROJECT_TABLE'))
        projects = project_table.scan()['Items']
        if not projects:
            return {'error': 'No projects found'}
        project_id = min(projects, key=lambda x: x['created_at'])['project_id']
    
    # Get cycles and variants
    cycle_table = dynamodb.Table(os.environ.get('CYCLE_TABLE'))
    variant_table = dynamodb.Table(os.environ.get('VARIANT_TABLE'))
    
    cycles = cycle_table.query(
        KeyConditionExpression='project_id = :pid',
        ExpressionAttributeValues={':pid': project_id}
    )['Items']
    
    variants = variant_table.query(
        KeyConditionExpression='project_id = :pid',
        ExpressionAttributeValues={':pid': project_id}
    )['Items']
    
    current_phase = determine_current_phase(cycles, variants)
    
    return {
        'project_id': project_id,
        'cycles_completed': len(cycles),
        'variants_generated': len(variants),
        'current_phase': current_phase,
        'cycles_summary': [{
            'cycle_number': int(c['cycle_number']),
            'best_kd_nm': float(c.get('best_kd_nm', 0)),
            'target_achieved': c.get('target_achieved', False)
        } for c in sorted(cycles, key=lambda x: int(x['cycle_number']))]
    }

def get_all_projects_status():
    """Get all projects status"""
    project_table = dynamodb.Table(os.environ.get('PROJECT_TABLE'))
    cycle_table = dynamodb.Table(os.environ.get('CYCLE_TABLE'))
    variant_table = dynamodb.Table(os.environ.get('VARIANT_TABLE'))
    
    projects = project_table.scan()['Items']
    all_cycles = cycle_table.scan()['Items']
    all_variants = variant_table.scan()['Items']
    
    project_statuses = []
    for project in projects:
        project_id = project['project_id']
        project_cycles = [c for c in all_cycles if c['project_id'] == project_id]
        project_variants = [v for v in all_variants if v['project_id'] == project_id]
        
        project_statuses.append({
            'project_id': project_id,
            'target_kd_nm': float(project.get('target_kd_nm', 0)),
            'cycles_completed': len(project_cycles),
            'variants_generated': len(project_variants),
            'current_phase': determine_current_phase(project_cycles, project_variants),
            'created_at': project.get('created_at')
        })
    
    return {
        'total_projects': len(projects),
        'projects': sorted(project_statuses, key=lambda x: x['created_at'])
    }

def determine_current_phase(cycles, variants):
    """Determine current phase"""
    if not cycles and not variants:
        return "Project planned - ready to start Cycle 1 Design"
    
    if not cycles:
        current_cycle = max([int(v.get('cycle_number', 1)) for v in variants])
        return f"Cycle {current_cycle} Design completed - ready for Make-Test"
    
    latest_cycle = max([int(c['cycle_number']) for c in cycles])
    next_cycle = latest_cycle + 1
    next_variants = [v for v in variants if int(v.get('cycle_number', 0)) == next_cycle]
    
    if next_variants:
        return f"Cycle {next_cycle} Design completed - ready for Make-Test"
    else:
        return f"Cycle {latest_cycle} completed - ready for Cycle {next_cycle} Design"