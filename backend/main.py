from fastapi import FastAPI, HTTPException, Depends
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel
from typing import List, Generator

app = FastAPI(title="Product CRUD API dengan FastAPI & Psycopg 3")

# 1. Konfigurasi Koneksi Database
DB_PARAMS = "dbname=kopdes user=postgres password=tIdakIngat host=localhost port=5432"

# 2. Dependency untuk Yield Koneksi Database
def get_db() -> Generator[psycopg.Connection, None, None]:
    """
    Membuka koneksi database per request, dan otomatis menutupnya
    setelah request selesai diproses.
    """
    with psycopg.connect(DB_PARAMS, row_factory=dict_row) as conn:
        yield conn
        # Context manager 'with' otomatis melakukan conn.close() di sini


# 3. Pydantic Schemas (Untuk Validasi Request & Response Body)
class ProductCreate(BaseModel):
    name: str
    available_amount: int
    price: float

class ProductUpdateStock(BaseModel):
    available_amount: int

class ProductResponse(BaseModel):
    id: int
    name: str
    available_amount: int
    price: float


# ==========================================
# ENDPOINTS / URL CRUD
# ==========================================

@app.get("/")
def read_root():
    return {"message": "Welcome to E-Commerce API, Bang!"}


# --- C - CREATE: Tambah Produk Baru ---
@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, conn: psycopg.Connection = Depends(get_db)):
    query = """
        INSERT INTO Products (name, available_amount, price)
        VALUES (%s, %s, %s)
        RETURNING id, name, available_amount, price;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (product.name, product.available_amount, product.price))
            new_product = cur.fetchone()
            conn.commit()  # Wajib commit untuk menyimpan data baru
            return new_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menambah produk: {str(e)}")


# --- R - READ: Ambil Semua Produk ---
@app.get("/products", response_model=List[ProductResponse])
def get_all_products(conn: psycopg.Connection = Depends(get_db)):
    query = "SELECT * FROM Products ORDER BY id ASC;"
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil data: {str(e)}")


# --- R - READ: Ambil Satu Produk Berdasarkan ID ---
@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, conn: psycopg.Connection = Depends(get_db)):
    query = "SELECT * FROM Products WHERE id = %s;"
    try:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))
            product = cur.fetchone()
            if not product:
                raise HTTPException(status_code=404, detail=f"Produk dengan ID {product_id} tidak ditemukan")
            return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- U - UPDATE: Ubah Stok Produk ---
@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product_stock(product_id: int, payload: ProductUpdateStock, conn: psycopg.Connection = Depends(get_db)):
    query = """
        UPDATE Products 
        SET available_amount = %s 
        WHERE id = %s
        RETURNING id, name, available_amount, price;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (payload.available_amount, product_id))
            updated_product = cur.fetchone()
            if not updated_product:
                raise HTTPException(status_code=404, detail=f"Produk dengan ID {product_id} tidak ditemukan")
            conn.commit()
            return updated_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- D - DELETE: Hapus Produk ---
@app.delete("/products/{product_id}", status_code=200)
def delete_product(product_id: int, conn: psycopg.Connection = Depends(get_db)):
    query = "DELETE FROM Products WHERE id = %s RETURNING id;"
    try:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail=f"Produk dengan ID {product_id} tidak ditemukan")
            conn.commit()
            return {"message": f"Produk dengan ID {product_id} berhasil dihapus"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))