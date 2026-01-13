'use client';

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
      <h1 className="text-4xl font-bold mb-8 text-center">CyberDrop Hub</h1>

      {/* ÁREA DE NEWSLETTER (Agora centralizada e única) */}
      <div className="max-w-md mx-auto mb-16">
        <NewsletterForm category="CYBER" />
      </div>

      <div className="grid gap-6">
        {loading ? (
          <p className="text-gray-500 text-center animate-pulse">Carregando notícias...</p>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="border p-6 rounded-lg shadow-sm hover:shadow-md transition bg-gray-900 text-white border-gray-800">
              
              {/* Badge sempre AZUL agora */}
              <span className="text-xs font-bold px-2 py-1 rounded bg-blue-600 text-white">
                {post.category}
              </span>

              <h2 className="text-2xl font-bold mt-3">{post.title}</h2>
              
              <p className="text-gray-400 mt-2 line-clamp-3 leading-relaxed">
                {post.content.substring(0, 150)}...
              </p>
              
              <a href={`/post/${post.slug}`} className="inline-block mt-4 text-blue-400 hover:text-blue-300 font-medium transition-colors">
                Ler mais →
              </a>
            </div>
          ))
        )}
      </div>
    </main>
  );
}