import sqlite3

conn = sqlite3.connect('uzflower.db')
cursor = conn.cursor()

# Check products
print("=== PRODUCTS ===")
cursor.execute("SELECT id, name, image_url FROM products LIMIT 5")
products = cursor.fetchall()
for p in products:
    print(f"ID: {p[0]}, Name: {p[1]}, Image: {p[2][:50] if p[2] else 'None'}...")

# Check product_images
print("\n=== PRODUCT_IMAGES ===")
cursor.execute("SELECT id, product_id, url FROM product_images LIMIT 10")
images = cursor.fetchall()
for img in images:
    print(f"ID: {img[0]}, Product ID: {img[1]}, URL: {img[2][:50] if img[2] else 'None'}...")

print(f"\nTotal products: {cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]}")
print(f"Total product images: {cursor.execute('SELECT COUNT(*) FROM product_images').fetchone()[0]}")

conn.close()
