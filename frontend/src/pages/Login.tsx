import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function Login({ onLogin }: { onLogin: (user: any) => void }) {
    const navigate = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (username && password) {
            try {
                const response = await fetch('http://localhost:8000/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password }),
                });

                if (response.ok) {
                    const data = await response.json();
                    alert('Login berhasil!');
                    onLogin(data.User);
                    navigate('/');
                } else {
                    const errorData = await response.json();
                    alert(errorData.detail || 'Login gagal');
                }
            } catch (error) {
                console.error('Error during login:', error);
                alert('Terjadi kesalahan saat login. Pastikan server berjalan.');
            }
        } else {
            alert('Mohon isi username dan password');
        }
    };

    return (
        <div className="login card">
            <h2>Login</h2>
            <form onSubmit={handleLogin} className="login-form">
                <div className="form-group">
                    <label>Username</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Masukkan username"
                    />
                </div>
                <div className="form-group">
                    <label>Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Masukkan password"
                    />
                </div>
                <button type="submit" className="login-btn">Masuk</button>
            </form>
        </div>
    );
}
