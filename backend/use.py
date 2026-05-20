import requests

# URL dasar dari FastAPI yang sedang berjalan
BASE_URL = "http://127.0.0.1:8000"

# ==========================================
# 1. TEST KONEKSI (GET /)
# ==========================================
def test_root():
    print("\n--- Testing Root Endpoint ---")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


# ==========================================
# 2. CREATE (POST /products)
# ==========================================
def create_product(name: str, available_amount: int, price: float):
    print(f"\n--- Menambahkan Produk: {name} ---")
    payload = {
        "name": name,
        "available_amount": available_amount,
        "price": price
    }
    response = requests.post(f"{BASE_URL}/products", json=payload)
    
    if response.status_code == 201:
        product_data = response.json()
        print(f" Sukses! Produk dibuat dengan ID: {product_data['id']}")
        return product_data['id']
    else:
        print(f"❌ Gagal! Status: {response.status_code}, Detail: {response.text}")
        return None


# ==========================================
# 3. READ ALL (GET /products)
# ==========================================
def get_all_products():
    print("\n--- Mengambil Semua Produk ---")
    response = requests.get(f"{BASE_URL}/products")
    
    if response.status_code == 200:
        products = response.json()
        print(f"Ditemukan {len(products)} produk:")
        for p in products:
            print(f"- ID {p['id']}: {p['name']} | Stok: {p['available_amount']} | Harga: Rp{p['price']}")
    else:
        print(f"❌ Gagal mengambil produk. Status: {response.status_code}")


# ==========================================
# 4. READ ONE (GET /products/{id})
# ==========================================
def get_product_by_id(product_id: int):
    print(f"\n--- Mengambil Detail Produk ID: {product_id} ---")
    response = requests.get(f"{BASE_URL}/products/{product_id}")
    
    if response.status_code == 200:
        print(f"Detail: {response.json()}")
    elif response.status_code == 404:
        print(f"⚠ Produk dengan ID {product_id} emang gak ada, Bang.")
    else:
        print(f"❌ Error: {response.status_code}")


# ==========================================
# 5. UPDATE STOCK (PUT /products/{id})
# ==========================================
def update_product_stock(product_id: int, new_stock: int):
    print(f"\n--- Mengubah Stok Produk ID: {product_id} Menjadi: {new_stock} ---")
    payload = {
        "available_amount": new_stock
    }
    response = requests.put(f"{BASE_URL}/products/{product_id}", json=payload)
    
    if response.status_code == 200:
        print(f" Sukses Update! Data terbaru: {response.json()}")
    else:
        print(f"❌ Gagal Update. Status: {response.status_code}")


# ==========================================
# 6. DELETE (DELETE /products/{id})
# ==========================================
def delete_product(product_id: int):
    print(f"\n--- Menghapus Produk ID: {product_id} ---")
    response = requests.delete(f"{BASE_URL}/products/{product_id}")
    
    if response.status_code == 200:
        print(f"🗑 {response.json()['message']}")
    else:
        print(f"❌ Gagal Hapus. Status: {response.status_code}")


# ==========================================
# Skenario Uji Coba Jalanin Semua Fungsi
# ==========================================
if __name__ == "__main__":
    # 1. Cek koneksi awal
    test_root()
    
    # 2. Tambah beberapa produk contoh
    id_rtx = create_product("Nvidia RTX 4090", 10, 35000000.0)
    id_mouse = create_product("Mouse Gaming Logitex", 100, 450000.0)
    
    # 3. Liat semua produk yang ada di DB sekarang
    get_all_products()
    
    if id_rtx:
        # 4. Cek detail satu produk (RTX 4090)
        get_product_by_id(id_rtx)
        
        # 5. Update stok RTX karena ada yang beli (stok sisa 9)
        update_product_stock(id_rtx, 9)
    
    if id_mouse:
        # 6. Hapus produk mouse
        delete_product(id_mouse)
        
    # 7. Liat list produk akhir setelah ada yang dihapus
    get_all_products()