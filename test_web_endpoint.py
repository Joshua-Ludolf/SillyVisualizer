import requests
import json
import base64

# Test code
test_code = """
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def main():
    x = 5
    result = factorial(x)
    print(f"Factorial of {x} is {result}")

if __name__ == "__main__":
    main()
"""

def test_web_endpoint():
    """Test the web endpoint with different diagram types"""
    url = "http://127.0.0.1:5000/visualize"
    
    for diagram_type in ['ast', 'cfg', 'ddg']:
        print(f"\n=== Testing {diagram_type.upper()} ===")
        
        payload = {
            'code': test_code,
            'language': 'python',
            'diagram_type': diagram_type
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if 'error' in data:
                print(f"❌ Error: {data['error']}")
            else:
                print(f"✅ Success: {data['title']}")
                print(f"   SVG data length: {len(data.get('svg_data', ''))}")
                print(f"   Diagram type: {data.get('diagram_type', 'unknown')}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_web_endpoint()
