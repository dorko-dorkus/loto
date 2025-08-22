'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '../../lib/api';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const res = await apiFetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (res.ok) {
      const data = (await res.json()) as { access_token: string };
      window.localStorage.setItem('token', data.access_token);
      router.push('/');
    }
  }

  return (
    <main>
      <form onSubmit={onSubmit}>
        <label>
          Username
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            type="text"
          />
        </label>
        <label>
          Password
          <input
            value={password}
            onChange={e => setPassword(e.target.value)}
            type="password"
          />
        </label>
        <button type="submit">Login</button>
      </form>
    </main>
  );
}
