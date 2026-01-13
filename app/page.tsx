'use client'; // 1. Transforma em componente do Cliente (roda no navegador)

import { supabase } from '@/lib/supabase';
import NewsletterForm from '@/components/NewsletterForm';
import { useEffect, useState } from 'react';

type Post = {
  id: number;
  title: string;
  category: string;
  content: string;
  slug: string;
  created_at: string;
};

export default function Home() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  // 2. O useEffect busca os dados assim que a tela abre
  useEffect(() => {
    const fetchPosts = async () => {
      const { data } = await supabase
        .from('posts')
        .select('*')
        .order('created_at', { ascending: false });
      
      if (data) {
        setPosts(data);
      }
      setLoading(false);
    };

    fetchPosts();
  }, []);

  return (
    <main className="max-w-4xl mx-auto p-10">
      <h1 className="text-4xl font-bold mb-8 text-center">Meu Hub de Conteúdo</h1>

      {/* AREA DE NEWSLETTER */}
      <div className="grid md:grid-cols-2 gap-6 mb-12">
        <NewsletterForm category="CYBER" />
        <NewsletterForm category="GAMES" />
      </div>

      <div className="grid gap-6">
        {loading ? (
          // Skeleton Loading (mostra algo enquanto carrega)
          <p className="text-gray-500 text-center animate-pulse">Carregando notícias...</p>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="border p-6 rounded-lg shadow-sm hover:shadow-md transition bg-gray-900 text-white">
              <span className={`text-xs font-bold px-2 py-1 rounded ${post.category === 'GAMES' ? 'bg-red-500' : 'bg-blue-500'}`}>
                {post.category}
              </span>
              <h2 className="text-2xl font-bold mt-2">{post.title}</h2>
              {/* Limitamos o texto para não ficar gigante na home */}
              <p className="text-gray-400 mt-2 line-clamp-3">
                {post.content.substring(0, 150)}...
              </p>
              <a href={`/post/${post.slug}`} className="inline-block mt-4 text-blue-300 hover:underline">
                Ler mais →
              </a>
            </div>
          ))
        )}
      </div>
    </main>
  );
}