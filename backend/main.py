from fastapi import FastAPI, HTTPException, Depends
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel
from typing import List, Generator

app = FastAPI(title="Product CRUD API dengan FastAPI & Psycopg 3")

# 1. Konfigurasi Koneksi Database
DB_PARAMS = "dbname=kopdes user=postgres password=tIdakIngat host=localhost port=5432"
MEMBER_DISCOUNT = 0.05

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

class CartAddProduct(BaseModel):
    userId: int
    productId: int
    quantity: int

class UseVoucher(BaseModel):
    userId: int
    voucherName: str
    
class Payment(BaseModel):
    userId: int
    voucherNames: list[str]

# ==========================================
# ENDPOINTS / URL CRUD
# ==========================================

@app.get("/")
def read_root():
    return {"message": "Welcome to E-Commerce API, Bang!"}


@app.get("/users/{id}")
def get_user(id, conn: psycopg.Connection = Depends(get_db)):
    query = f"SELECT * FROM users where \"id\"={id};"
    try:
        with  conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()[0]
    except Exception as e:
        return HTTPException(status_code=500, detail=f"User Not Found: {e}")
    
# --- R - READ: Ambil Semua Produk ---
@app.get("/products", response_model=List[ProductResponse])
def get_all_products(conn: psycopg.Connection = Depends(get_db)):
    query = "SELECT * FROM Products ORDER BY name ASC;"
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil data: {str(e)}")

@app.post('/cart/add/product')
def add_product_to_cart(datas: CartAddProduct, conn: psycopg.Connection = Depends(get_db)):
    query = """
        INSERT INTO carts (user_id, product_id, quantity)
        VALUES (%s, %s, %s);
    """
    select_query = """
        SELECT id, quantity FROM carts
        where user_id=%s
            AND product_id=%s
            AND is_paid=false;
    """
    select_product_query = """
        SELECT available_amount FROM products
        WHERE id = %s;
    """
    
    update_query = """
        UPDATE carts
        SET quantity = quantity+%s
        WHERE id = %s; 
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(select_query, (datas.userId, datas.productId))
            res = cur.fetchone()
            cur.execute(select_product_query, (datas.productId,))
            product = cur.fetchone()
            if res==None:
                if (product["available_amount"]<datas.quantity):
                    return {"Status":"Failed", "Message": "Gagal Menambahkan Produk, Jumlah Produk yang Tersedia Tidak Mencukupi"}
                cur.execute(query, (datas.userId, datas.productId, datas.quantity))
                # Wajib commit untuk menyimpan data baru
            else:
                if (product["available_amount"]<res["quantity"]+datas.quantity):
                    return {"Status":"Failed", "Message": "Gagal Menambahkan Produk, Jumlah Produk yang Tersedia Tidak Mencukupi"}
                cur.execute(update_query, (datas.quantity, res['id']))
            conn.commit()
            return {"Status":"Success", "Message": "Berhasil Menambahkan Produk di Keranjang"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menambah produk: {str(e)}")

@app.get('/cart/{userId}')
def get_cart(userId: int, conn: psycopg.Connection = Depends(get_db)):
    query = """
        SELECT p.id, p.name, p.description, p.price, c.quantity FROM carts as c
        INNER JOIN products as p ON c.product_id = p.id
        WHERE user_id=%s
        AND is_paid=false;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (userId,))
            cart_products = cur.fetchall()
            return cart_products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil keranjang: {str(e)}")

@app.post('/use/voucher')
def use_voucher(datas: UseVoucher, conn: psycopg.Connection = Depends(get_db)):
    query = """
        SELECT v.id FROM usedVouchers as uv
        INNER JOIN vouchers as v 
        ON uv.voucher_id = v.id
        WHERE user_id=%s
        AND v.id=%s;
    """
    select_voucher_query="""
        SELECT * FROM vouchers
        WHERE name = %s;
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(select_voucher_query, (datas.voucherName,))
            vouchers = res = cur.fetchall()
            if len(vouchers)==0:
                return {"Status":"Failed", "Message":"Voucher Tidak Ada"}
            voucher = vouchers[0]
            cur.execute(query, (datas.userId, voucher["id"]))
            res = cur.fetchall()
            if len(res)!=0:
                return {"Status":"Failed", "Message":"Voucher Telah Digunakan"}
            return {"Status":"Success", "Message":"Voucher Berhasil Digunakan"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal saat menggunakan voucher: {str(e)}")

from enum import Enum
class VoucherType(Enum):
    FIXED_MINUS = "FIXED_MINUS"
    PERCENTAGE_DISCOUNT='PERCENTAGE_DISCOUNT'
    FIXED_CASHBACK='FIXED_CASHBACK'
def handle_voucher(total_price: float, voucher_type: str, amount: float)->tuple[float, float]:
    cashback = 0
    match voucher_type:
        case VoucherType.FIXED_MINUS.value:
            total_price-=amount
        case VoucherType.PERCENTAGE_DISCOUNT.value:
            total_price*=(1-(amount/100))
        case VoucherType.FIXED_CASHBACK.value:
            cashback=amount
        case _:
            raise ValueError("Unknown Value in Voucher Type")
    return (total_price, cashback)

@app.post('/cart/pay')
def payment_handle( datas: Payment, conn: psycopg.Connection = Depends(get_db)):
    user_query = """
        SELECT id, is_member, balance FROM users
        WHERE id=%s;
    """
    cart_query = """
        SELECT c.id, c.product_id, p.price, c.quantity, 
        CASE 
            WHEN c.quantity > p.available_amount THEN 1 
            ELSE 0 
        END AS is_exceed
        FROM carts as c
        INNER JOIN products as p ON c.product_id = p.id
        WHERE user_id=%s
        AND is_paid=false;
    """
    vouchers_query = """
        SELECT v.id, v.effect, v.amount 
        FROM vouchers AS v
        WHERE v.name = ANY(%s)
          AND NOT EXISTS (
              SELECT 1 
              FROM usedVouchers AS uv 
              WHERE uv.voucher_id = v.id 
                AND uv.user_id = %s
          )
        ORDER BY v.effect DESC;
    """
    
    user_change_balance_query = """
        UPDATE users
        SET balance = %s
        WHERE id = %s
    """
    cart_paid = """
        UPDATE carts
        SET is_paid = true
        WHERE id = ANY(%s)
    """
    
    used_vouchers_insert = """
        INSERT INTO usedVouchers (user_id, voucher_id) 
        VALUES (%s, %s)
    """
    update_product_stock_query = """
        UPDATE products 
        SET available_amount = available_amount - %s
        WHERE id=%s;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(user_query, (datas.userId,))
            user = cur.fetchone()
            if user==None:
                return {"Status":"Failed", "Message":"User Tidak Ditemukan"}
            cur.execute(cart_query, (datas.userId,))
            cart_products = cur.fetchall()
            if len(cart_products)==0:
                return {"Status":"Failed", "Message":"Belum Ada Produk di Keranjang"}
            # Calculate if quantity more than available product
            total = 0
            for product in cart_products:
                if (product["is_exceed"]==1):
                    return {"Status":"Failed", "Message":"Jumlah Produk yang Akan Dibeli Melebihi Stok yang Ada"}
                total+=(product["price"]*product["quantity"])
            # Do Discount
            cur.execute(vouchers_query, (datas.voucherNames, datas.userId))
            vouchers = cur.fetchall()
            cashback = 0
            for voucher in vouchers:
                total, cashback_amount = handle_voucher(total_price=total,
                                            voucher_type=voucher["effect"], amount=voucher["amount"])
                cashback+=cashback_amount
            if (user["is_member"]):
                total*=(1-MEMBER_DISCOUNT)
            if total>user["balance"]:
                return {"Status":"Failed", "Message":"Saldo Anda Tidak Mencukupi"}
            user["balance"]-=total
            
            user["balance"]+=cashback
            
            cur.executemany(used_vouchers_insert,
                            [(datas.userId, vouchers[i]["id"]) for i in range(len(vouchers))]
                            )
            cur.execute(user_change_balance_query, (user["balance"],user["id"]))
            cart_ids = [product["id"] for product in cart_products]
            cur.execute(cart_paid, (cart_ids,))
            # Dont forget subtract available product
            product_id_subtract = [(product["quantity"], product["product_id"]) for product in cart_products]
            cur.executemany(update_product_stock_query, product_id_subtract)
            conn.commit()
            return {"Status":"Success", "Message":"Keranjang Anda Berhasil Dibayar"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membayar: {str(e)}")