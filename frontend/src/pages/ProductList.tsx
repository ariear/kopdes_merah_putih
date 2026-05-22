import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Product } from '../types';

export function ProductList() {
    const navigate = useNavigate();
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('http://localhost:8000/products')
            .then(res => res.json())
            .then(data => {
                // Add placeholder image
                const productsWithImage = data.map((p: any) => ({
                    ...p,
                    image: `https://placehold.co/400x300/ff5e5b/000?text=${p.name.toUpperCase().replace(/ /g, '+')}`
                }));
                setProducts(productsWithImage);
                setLoading(false);
            })
            .catch(err => {
                console.error('Failed to fetch products:', err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <div className="product-list"><h2>Loading...</h2></div>;
    }

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
