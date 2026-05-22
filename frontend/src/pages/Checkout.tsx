interface PaymentDetail {
    subtotal: number;
    voucher_discount: number;
    member_discount: number;
    cashback: number;
    total_paid: number;
    new_balance: number;
}

export function Checkout({ paymentResult, resetFlow }: {
    paymentResult: PaymentDetail | null;
    resetFlow: () => void;
}) {
    return (
        <div className="checkout card">
            <h2>Pembayaran Berhasil!</h2>
            <div className="success-box">
                <p>Terima kasih telah berbelanja di Kopdes Merah Putih.</p>

                {paymentResult ? (
                    <div className="payment-detail">
                        <div className="detail-row">
                            <span>Subtotal:</span>
                            <span>Rp {paymentResult.subtotal.toLocaleString('id-ID')}</span>
                        </div>
                        {paymentResult.voucher_discount > 0 && (
                            <div className="detail-row discount">
                                <span>Diskon Voucher:</span>
                                <span>- Rp {paymentResult.voucher_discount.toLocaleString('id-ID')}</span>
                            </div>
                        )}
                        {paymentResult.member_discount > 0 && (
                            <div className="detail-row discount">
                                <span>Diskon Member (5%):</span>
                                <span>- Rp {paymentDetail_format(paymentResult.member_discount)}</span>
                            </div>
                        )}
                        {paymentResult.cashback > 0 && (
                            <div className="detail-row cashback">
                                <span>Cashback diterima:</span>
                                <span>+ Rp {paymentResult.cashback.toLocaleString('id-ID')}</span>
                            </div>
                        )}
                        <div className="detail-row total">
                            <span>Total Dibayar:</span>
                            <span>Rp {paymentResult.total_paid.toLocaleString('id-ID')}</span>
                        </div>
                        <div className="detail-row balance">
                            <span>Saldo Baru:</span>
                            <span>Rp {paymentResult.new_balance.toLocaleString('id-ID')}</span>
                        </div>
                    </div>
                ) : (
                    <p className="total-paid">Pembayaran berhasil diproses.</p>
                )}
            </div>
            <button onClick={resetFlow} className="home-btn">Kembali ke Beranda</button>
        </div>
    );
}

function paymentDetail_format(value: number): string {
    return value.toLocaleString('id-ID');
}
