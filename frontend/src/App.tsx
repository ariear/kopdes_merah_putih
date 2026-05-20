import { useState } from 'react';
import { Routes, Route, Link, useNavigate, useParams, useLocation } from 'react-router-dom';
import './App.css';

type Product = {
  id: number;
  name: string;
  price: number;
  description: string;
  image: string;
};

type CartItem = {
  product: Product;
  qty: number;
};

const products: Product[] = [
  {
    id: 1,
    name: 'Sepatu Kets Super',
    price: 250000,
    description: 'Sepatu kets nyaman untuk jalan-jalan dan gaya.',
    image: 'https://placehold.co/400x300/ff5e5b/000?text=SEPATU'
  },
  {
    id: 2,
    name: 'Tas Ransel Anti Air',
    price: 350000,
    description: 'Tas ransel kuat dan tahan air untuk petualanganmu.',
    image: 'https://placehold.co/400x300/00cecb/000?text=TAS'
  },
  {
    id: 3,
    name: 'Topi Keren',
    price: 75000,
    description: 'Topi dengan desain kekinian untuk melindungi dari panas.',
    image: 'https://placehold.co/400x300/ffed66/000?text=TOPI'
  }
];

function App() {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isMember, setIsMember] = useState<boolean>(false);
  const [voucher, setVoucher] = useState<string>('');
  const [appliedVouchers, setAppliedVouchers] = useState<string[]>([]);
  const [balance, setBalance] = useState<number>(0);
  const [showPopup, setShowPopup] = useState<boolean>(false);

  const navigate = useNavigate();
  const location = useLocation();

  const handleAddToCart = (product: Product, qty: number) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product.id === product.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.product.id === product.id
            ? { ...item, qty: item.qty + qty }
            : item
        );
      } else {
        return [...prevCart, { product, qty }];
      }
    });

    setShowPopup(true);
    setTimeout(() => setShowPopup(false), 2000);
  };

  const handleApplyVoucher = () => {
    const code = voucher.toUpperCase();
    if (code === 'DISKON50' || code === 'CASHBACK20') {
      if (appliedVouchers.includes(code)) {
        alert('Voucher ini sudah digunakan!');
      } else {
        setAppliedVouchers([...appliedVouchers, code]);
        setVoucher('');
        alert('Voucher berhasil digunakan!');
      }
    } else {
      alert('Voucher tidak valid!');
    }
  };

  const calculateSubtotal = () => {
    return cart.reduce((total, item) => total + (item.product.price * item.qty), 0);
  };

  const calculateTotal = () => {
    let total = calculateSubtotal();

    if (isMember) {
      total = total * 0.9; // 10% member discount
    }

    if (appliedVouchers.includes('DISKON50')) {
      total = total - 50000; // 50k discount
    }

    return Math.max(0, total);
  };

  const handleCheckout = () => {
    if (cart.length === 0) {
      alert('Keranjang belanja kosong!');
      return;
    }

    if (appliedVouchers.includes('CASHBACK20')) {
      setBalance(prev => prev + 20000);
    }

    navigate('/checkout');
  };

  const resetFlow = () => {
    setCart([]);
    setIsMember(false);
    setVoucher('');
    setAppliedVouchers([]);
    navigate('/');
  };

  const cartItemCount = cart.reduce((count, item) => count + item.qty, 0);
  const isProductActive = location.pathname === '/' || location.pathname.startsWith('/product');
  const isCartActive = location.pathname === '/cart';

  return (
    <div className="container">
      <header className="header">
        <div className="header-top">
          <h1>Kopdes Merah Putih</h1>
          <div className="balance-badge">Saldo: Rp {balance.toLocaleString('id-ID')}</div>
        </div>
        <div className="step-indicator">
          <Link to="/" className={`nav-item ${isProductActive ? 'active' : ''}`}>Produk</Link>
          <Link to="/cart" className={`nav-item ${isCartActive ? 'active' : ''}`}>
            Keranjang {cartItemCount > 0 && `(${cartItemCount})`}
          </Link>
        </div>
      </header>

      {showPopup && (
        <div className="popup-notification">
          Berhasil ditambahkan ke keranjang!
        </div>
      )}

      <Routes>
        <Route path="/" element={<ProductList />} />
        <Route path="/product/:id" element={<ProductDetail onAddToCart={handleAddToCart} />} />
        <Route path="/cart" element={
          <Cart
            cart={cart}
            isMember={isMember}
            setIsMember={setIsMember}
            voucher={voucher}
            setVoucher={setVoucher}
            appliedVouchers={appliedVouchers}
            handleApplyVoucher={handleApplyVoucher}
            calculateSubtotal={calculateSubtotal}
            calculateTotal={calculateTotal}
            handleCheckout={handleCheckout}
          />
        } />
        <Route path="/checkout" element={
          <Checkout
            calculateTotal={calculateTotal}
            appliedVouchers={appliedVouchers}
            resetFlow={resetFlow}
          />
        } />
      </Routes>
    </div>
  );
}

function ProductList() {
  const navigate = useNavigate();
  return (
    <div className="product-list">
      <h2>Daftar Produk</h2>
      <div className="grid">
        {products.map(p => (
          <div key={p.id} className="card product-card">
            <img src={p.image} alt={p.name} className="product-image" />
            <h3>{p.name}</h3>
            <p className="price">Rp {p.price.toLocaleString('id-ID')}</p>
            <button onClick={() => navigate(`/product/${p.id}`)}>Pilih</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProductDetail({ onAddToCart }: { onAddToCart: (product: Product, qty: number) => void }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [qty, setQty] = useState(1);

  const product = products.find(p => p.id === Number(id));

  if (!product) {
    return <div>Produk tidak ditemukan</div>;
  }

  return (
    <div className="product-detail card">
      <button className="back-btn" onClick={() => navigate('/')}>&lt; Kembali</button>
      <div className="detail-content">
        <img src={product.image} alt={product.name} className="detail-image" />
        <div className="detail-info">
          <h2>{product.name}</h2>
          <p className="price">Rp {product.price.toLocaleString('id-ID')}</p>
          <p className="desc">{product.description}</p>

          <div className="qty-selector">
            <label>Jumlah:</label>
            <div className="qty-controls">
              <button onClick={() => setQty(Math.max(1, qty - 1))}>-</button>
              <input type="number" value={qty} readOnly />
              <button onClick={() => setQty(qty + 1)}>+</button>
            </div>
          </div>

          <button className="add-to-cart-btn" onClick={() => onAddToCart(product, qty)}>Tambah ke Keranjang</button>
        </div>
      </div>
    </div>
  );
}

function Cart({
  cart, isMember, setIsMember, voucher, setVoucher, appliedVouchers,
  handleApplyVoucher, calculateSubtotal, calculateTotal, handleCheckout
}: any) {
  return (
    <div className="cart card">
      <h2>Keranjang Belanja</h2>

      {cart.length === 0 ? (
        <p className="empty-cart">Keranjang Anda masih kosong.</p>
      ) : (
        <>
          <div className="cart-items">
            {cart.map((item: CartItem) => (
              <div key={item.product.id} className="cart-item">
                <div className="cart-item-info">
                  <h3>{item.product.name}</h3>
                  <p>Rp {item.product.price.toLocaleString('id-ID')} x {item.qty}</p>
                </div>
                <div className="cart-item-total">
                  <p>Rp {(item.product.price * item.qty).toLocaleString('id-ID')}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="member-check">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isMember}
                onChange={(e) => setIsMember(e.target.checked)}
              />
              <span className="checkbox-custom"></span>
              Saya adalah Member (Diskon 10%)
            </label>
          </div>

          <div className="voucher-section">
            <label>Punya Voucher?</label>
            <div className="voucher-input-group">
              <input
                type="text"
                placeholder="Masukkan kode (DISKON50 / CASHBACK20)"
                value={voucher}
                onChange={(e) => setVoucher(e.target.value)}
              />
              <button onClick={handleApplyVoucher}>Terapkan</button>
            </div>
            {appliedVouchers.includes('DISKON50') && <p className="success-text">Voucher DISKON50 diterapkan! (Potongan Rp 50.000)</p>}
            {appliedVouchers.includes('CASHBACK20') && <p className="success-text">Voucher CASHBACK20 diterapkan! (Cashback Rp 20.000 ke Saldo)</p>}
          </div>

          <div className="cart-summary">
            <div className="summary-row">
              <span>Subtotal:</span>
              <span>Rp {calculateSubtotal().toLocaleString('id-ID')}</span>
            </div>
            {isMember && (
              <div className="summary-row discount">
                <span>Diskon Member (10%):</span>
                <span>- Rp {(calculateSubtotal() * 0.1).toLocaleString('id-ID')}</span>
              </div>
            )}
            {appliedVouchers.includes('DISKON50') && (
              <div className="summary-row discount">
                <span>Voucher (DISKON50):</span>
                <span>- Rp 50.000</span>
              </div>
            )}
            {appliedVouchers.includes('CASHBACK20') && (
              <div className="summary-row cashback">
                <span>Cashback (CASHBACK20):</span>
                <span>+ Rp 20.000 ke Saldo</span>
              </div>
            )}
            <div className="summary-row total">
              <span>Total Bayar:</span>
              <span>Rp {calculateTotal().toLocaleString('id-ID')}</span>
            </div>
          </div>

          <button className="checkout-btn" onClick={handleCheckout}>Proses Pembayaran</button>
        </>
      )}
    </div>
  );
}

function Checkout({ calculateTotal, appliedVouchers, resetFlow }: any) {
  return (
    <div className="checkout card">
      <h2>Pembayaran Berhasil!</h2>
      <div className="success-box">
        <p>Terima kasih telah berbelanja di Kopdes Merah Putih.</p>
        <p className="total-paid">Total yang dibayar: Rp {calculateTotal().toLocaleString('id-ID')}</p>
        {appliedVouchers.includes('CASHBACK20') && (
          <p className="cashback-notice">Cashback Rp 20.000 telah ditambahkan ke Saldo Anda!</p>
        )}
      </div>
      <button onClick={resetFlow} className="home-btn">Kembali ke Beranda</button>
    </div>
  );
}

export default App;
