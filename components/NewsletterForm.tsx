'use client'; // Necessário pois tem interação (digitar, clicar)

import { useState } from 'react';

export default function NewsletterForm({ category }: { category: 'GAMES' | 'CYBER' }) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('loading');

    const res = await fetch('/api/subscribe', {
      method: 'POST',
      body: JSON.stringify({ email, category }),
    });

    if (res.ok) {
      setStatus('success');
      setEmail('');
    } else {
      setStatus('error');
    }
  }

  return (
    <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 mt-8">
      <h3 className="text-xl font-bold text-white mb-2">
        Receba notícias de <span className={category === 'GAMES' ? 'text-red-500' : 'text-blue-500'}>{category}</span>
      </h3>
      <p className="text-gray-400 text-sm mb-4">
        Resumos diretos no seu e-mail. Sem spam.
      </p>

      {status === 'success' ? (
        <div className="text-green-400 font-bold bg-green-900/20 p-3 rounded">
          ✅ Inscrito com sucesso! Cheque seu e-mail.
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="email"
            placeholder="seu@email.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="flex-1 bg-black border border-gray-700 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={status === 'loading'}
            className="bg-white text-black px-6 py-2 rounded font-bold hover:bg-gray-200 disabled:opacity-50"
          >
            {status === 'loading' ? '...' : 'Assinar'}
          </button>
        </form>
      )}
      {status === 'error' && <p className="text-red-400 text-xs mt-2">Erro ao inscrever. Tente novamente.</p>}
    </div>
  );
}