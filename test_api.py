import requests
import json

# Test the endpoint directly
test_data = {
    'code': 'def hello(): return 42',
    'language': 'python', 
    'diagram_type': 'ast'
}

try:
    response = requests.post('http://127.0.0.1:5000/visualize', json=test_data)
    print('Status:', response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print('Response keys:', list(data.keys()))
        if 'graph_data' in data:
            graph_data = data['graph_data']
            print('Graph data keys:', list(graph_data.keys()))
            print('Nodes count:', len(graph_data['nodes']))
            print('Links count:', len(graph_data['links']))
            if graph_data['nodes']:
                print('First node:', graph_data['nodes'][0])
        else:
            print('No graph_data in response')
            print('Response:', data)
    else:
        print('Error:', response.text)
        
except Exception as e:
    print('Error:', e)
