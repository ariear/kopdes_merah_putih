import psycopg
from psycopg.rows import dict_row

# 1. Konfigurasi Koneksi Database
DB_PARAMS = "dbname=kopdes user=postgres password=tIdakIngat host=localhost port=5432"


def get_db_connection():
    """Fungsi untuk membuka koneksi ke PostgreSQL"""
    # Menggunakan dict_row agar hasil SELECT berbentuk dictionary (bukan tuple)
    return psycopg.connect(DB_PARAMS, row_factory=dict_row)


def get_all_products():
    query = "SELECT * FROM Products;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        print(f"❌ Gagal mengambil semua produk: {e}")
        return []

# ==========================================
# C - CREATE (Tambah Produk Baru)
# ==========================================
def create_product(name, available_amount, price):
    query = """
        INSERT INTO Products (name, available_amount, price)
        VALUES (%s, %s, %s)
        RETURNING id;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name, available_amount, price))
                # Mengambil ID produk yang baru saja dibuat
                product_id = cur.fetchone()["id"]
                conn.commit()  # Wajib commit untuk query INSERT/UPDATE/DELETE
                print(f" Sukses menambahkan produk dengan ID: {product_id}")
                return product_id
    except Exception as e:
        print(f"❌ Gagal menambahkan produk: {e}")
        return None


# ==========================================
# R - READ (Ambil Data Produk)
# ==========================================



def get_product_by_id(product_id):
    query = "SELECT * FROM Products WHERE id = %s;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (product_id,))
                return cur.fetchone()
    except Exception as e:
        print(f"❌ Gagal mengambil produk ID {product_id}: {e}")
        return None


# ==========================================
# U - UPDATE (Ubah Data Produk)
# ==========================================
def update_product_stock(product_id, new_amount):
    query = """
        UPDATE Products 
        SET available_amount = %s 
        WHERE id = %s;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (new_amount, product_id))
                conn.commit()
                print(f" Sukses mengupdate stok produk ID {product_id} menjadi {new_amount}")
                return True
    except Exception as e:
        print(f"❌ Gagal mengupdate produk: {e}")
        return False


# ==========================================
# D - DELETE (Hapus Produk)
# ==========================================
def delete_product(product_id):
    query = "DELETE FROM Products WHERE id = %s;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (product_id,))
                conn.commit()
                print(f" Sukses menghapus produk ID {product_id}")
                return True
    except Exception as e:
        print(f"❌ Gagal menghapus produk: {e}")
        return False


# ==========================================
# CONTOH CARA PENGGUNAAN (TEST RUN)
# ==========================================
if __name__ == "__main__":
    print("--- 1. Menambahkan Produk Baru ---")
    id_sepatu = create_product("Sepatu Gacor", 50, 150000.0)
    id_baju = create_product("Kaos Polos", 100, 45000.0)

    print("\n--- 2. Membaca Semua Produk ---")
    semua_produk = get_all_products()
    for produk in semua_produk:
        print(produk)

    print("\n--- 3. Mengupdate Stok Produk ---")
    if id_sepatu:
        update_product_stock(id_sepatu, 45)  # Stok berkurang jadi 45

    print("\n--- 4. Membaca Satu Produk Spesifik ---")
    if id_sepatu:
        produk_spesifik = get_product_by_id(id_sepatu)
        print(produk_spesifik)

    print("\n--- 5. Menghapus Produk ---")
    if id_baju:
        delete_product(id_baju)