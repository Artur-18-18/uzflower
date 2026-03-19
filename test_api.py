import requests

# Test API endpoint
response = requests.get('http://localhost:8000/api/products')
if response.status_code == 200:
    products = response.json()
    print(f"Total products: {len(products)}")
    
    for p in products:
        images_count = len(p.get('images', []))
        if images_count > 0:
            print(f"\nProduct ID={p['id']}, Name={p['name']}")
            print(f"  Main image: {p['image_url'][:50] if p['image_url'] else 'None'}...")
            print(f"  Additional images: {images_count}")
            for i, img in enumerate(p['images'][:3], 1):
                print(f"    {i}. {img[:60]}...")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
