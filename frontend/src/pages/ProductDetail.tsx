import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { Product } from '../types';

export function ProductDetail({ onAddToCart }: { onAddToCart: (product: Product, qty: number) => void }) {
    const { id } = useParams();
    const navigate = useNavigate();
    const [qty, setQty] = useState(1);
    const [product, setProduct] = useState<Product | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`http://localhost:8000/products/${id}`)
            .then(res => {
                if (!res.ok) throw new Error('Product not found');
                return res.json();
            })
            .then(data => {
                setProduct({
                    ...data,
                    image: `https://placehold.co/400x300/ff5e5b/000?text=${data.name.toUpperCase().replace(/ /g, '+')}`
                });
                setLoading(false);
            })
            .catch(err => {
                console.error('Failed to fetch product:', err);
                setLoading(false);
            });
    }, [id]);

    if (loading) {
        return <div className="product-detail card"><h2>Loading...</h2></div>;
    }

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
                    <p className="stock">Stok tersedia: {product.available_amount}</p>

                    <div className="qty-selector">
                        <label>Jumlah:</label>
                        <div className="qty-controls">
                            <button onClick={() => setQty(Math.max(1, qty - 1))}>-</button>
                            <input type="number" value={qty} readOnly />
                            <button onClick={() => setQty(Math.min(product.available_amount, qty + 1))}>+</button>
                        </div>
                    </div>

                    <button className="add-to-cart-btn" onClick={() => onAddToCart(product, qty)}>Tambah ke Keranjang</button>
                </div>
            </div>
        </div>
    );
}
