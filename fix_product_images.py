import sqlite3

conn = sqlite3.connect('uzflower.db')
cursor = conn.cursor()

# Find products without main image but with additional images
print("=== Products with NULL product_id in product_images ===")
cursor.execute("""
    SELECT id, url FROM product_images 
    WHERE product_id IS NULL 
    ORDER BY id
""")
orphan_images = cursor.fetchall()

print(f"Found {len(orphan_images)} orphan images")

# Get first product to assign images to (for testing)
cursor.execute("SELECT id, name FROM products LIMIT 1")
first_product = cursor.fetchone()

if first_product and orphan_images:
    print(f"\nAssigning orphan images to product: {first_product[0]} - {first_product[1]}")
    
    # Assign first 3 images to this product
    for i, (img_id, url) in enumerate(orphan_images[:3]):
        cursor.execute("""
            UPDATE product_images 
            SET product_id = ? 
            WHERE id = ?
        """, (first_product[0], img_id))
        print(f"  Updated image {img_id} -> product {first_product[0]}")

    conn.commit()
    print("\nDone! Check the database again.")
else:
    print("No products or no orphan images found.")

conn.close()
