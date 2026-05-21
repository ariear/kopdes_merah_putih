import psycopg
from psycopg.rows import dict_row

DB_PARAMS = "dbname=kopdes user=postgres password=tIdakIngat host=localhost port=5432"

def get_db_connection():
    return psycopg.connect(DB_PARAMS, row_factory=dict_row)

# ==========================================
# REVISI SEEDING DATA (Sesuai Skema Baru)
# ==========================================
def seed_database():
    """Fungsi seeding yang disesuaikan dengan skema Users, Products, dan Vouchers Anda"""
    
    # 1. Data sesuai kolom: name, is_member, balance
    users_data = [
        ("Budi Santoso", True, 150000.0),
        ("Siti Aminah", False, 0.0),
        ("Andi Wijaya", True, 500000.0)
    ]
    
    # 2. Data sesuai kolom: name, available_amount, price
    products_data = [
        ("Sepatu Gacor", 50, 150000.0, "Sepatu lari lokal yang sangat nyaman dan trendi untuk dipakai harian."),
        ("Kaos Polos", 100, 45000.0, "Kaos polos berbahan Combed 30s yang adem dan menyerap keringat."),
        ("Jaket Hoodie", 30, 250000.0, "Hoodie tebal dengan bahan fleece premium, cocok untuk cuaca dingin.")
    ]
    
    # 3. Data sesuai kolom: name, effect (enum), amount
    # Catatan: Pastikan tipe ENUM untuk 'effect' sudah dibuat di database Anda
    vouchers_data = [
        ("DISKON_FLAT", "FIXED_MINUS", 10000.0), 
        ("PERSEN_ANAK_EMAS", "PERCENTAGE_DISCOUNT", 15.0),
        ("CASHBACK_MANTAP", "FIXED_CASHBACK", 20000.0)
    ]

    print("--- Memulai Proses Seeding Database ---")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                
                # --- OPTIONAL CLEANUP ---
                # cur.execute("TRUNCATE TABLE Users, Products, Vouchers RESTART IDENTITY CASCADE;")
                
                # Seeding Tabel Users
                cur.executemany("""
                    INSERT INTO Users (name, is_member, balance) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, users_data)
                print(" Data tabel Users berhasil diproses.")

                # Seeding Tabel Products
                cur.executemany("""
                    INSERT INTO Products (name, available_amount, price, description) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, products_data)
                print(" Data tabel Products berhasil diproses.")

                # Seeding Tabel Vouchers
                cur.executemany("""
                    INSERT INTO Vouchers (name, effect, amount) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, vouchers_data)
                print(" Data tabel Vouchers berhasil diproses.")
                
                conn.commit()
                print(" Seeding selesai dengan sukses!")
                
    except Exception as e:
        print(f"❌ Gagal melakukan seeding: {e}")

if __name__ == "__main__":
    seed_database()