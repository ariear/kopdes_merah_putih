import type { CartItem } from '../types';

interface CartSummary {
    subtotal: number;
    voucher_discount: number;
    member_discount: number;
    cashback: number;
    total_to_pay: number;
}

export function Cart({
    cart, isMember, voucher, setVoucher, appliedVouchers,
    handleApplyVoucher, calculateSubtotal, calculateTotal, cartSummary, handleCheckout
}: {
    cart: CartItem[];
    isMember: boolean;
    voucher: string;
    setVoucher: (v: string) => void;
    appliedVouchers: string[];
    handleApplyVoucher: () => void;
    calculateSubtotal: () => number;
    calculateTotal: () => number;
    cartSummary: CartSummary | null;
    handleCheckout: () => void;
}) {
    const subtotal = cartSummary ? cartSummary.subtotal : calculateSubtotal();
    const total = cartSummary ? cartSummary.total_to_pay : calculateTotal();

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

                    <div className="voucher-section">
                        <label>Punya Voucher?</label>
                        <div className="voucher-input-group">
                            <input
                                type="text"
                                placeholder="Masukkan kode voucher"
                                value={voucher}
                                onChange={(e) => setVoucher(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleApplyVoucher()}
                            />
                            <button onClick={handleApplyVoucher}>Terapkan</button>
                        </div>
                        {appliedVouchers.length > 0 && (
                            <div className="applied-vouchers">
                                {appliedVouchers.map(v => (
                                    <span key={v} className="voucher-tag">✓ {v}</span>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="cart-summary">
                        <div className="summary-row">
                            <span>Subtotal:</span>
                            <span>Rp {subtotal.toLocaleString('id-ID')}</span>
                        </div>

                        {cartSummary && cartSummary.voucher_discount > 0 && (
                            <div className="summary-row discount">
                                <span>Diskon Voucher:</span>
                                <span>- Rp {cartSummary.voucher_discount.toLocaleString('id-ID')}</span>
                            </div>
                        )}

                        {(cartSummary ? cartSummary.member_discount > 0 : isMember) && (
                            <div className="summary-row discount">
                                <span>Diskon Member (5%):</span>
                                <span>- Rp {(cartSummary ? cartSummary.member_discount : subtotal * 0.05).toLocaleString('id-ID')}</span>
                            </div>
                        )}

                        {cartSummary && cartSummary.cashback > 0 && (
                            <div className="summary-row cashback">
                                <span>Cashback (ke Saldo):</span>
                                <span>+ Rp {cartSummary.cashback.toLocaleString('id-ID')}</span>
                            </div>
                        )}

                        <div className="summary-row total">
                            <span>Total Bayar:</span>
                            <span>Rp {total.toLocaleString('id-ID')}</span>
                        </div>
                    </div>

                    <button className="checkout-btn" onClick={handleCheckout}>Proses Pembayaran</button>
                </>
            )}
        </div>
    );
}
