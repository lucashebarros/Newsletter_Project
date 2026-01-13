import { supabase } from '@/lib/supabase';

export const runtime = 'edge';

// Isso diz ao Next.js para atualizar essa página a cada 60 segundos (ISR)
export const dynamic = 'force-dynamic';

export default async function Home() {
  // Busca os posts no Supabase
  const { data: posts } = await supabase
    .from('posts')
    .select('*')
    .order('created_at', { ascending: false });

  return (
    <main className="max-w-4xl mx-auto p-10">
      <h1 className="text-4xl font-bold mb-8 text-center">Meu Hub de Conteúdo</h1>

      <div className="grid gap-6">
        {posts?.map((post) => (
          <div key={post.id} className="border p-6 rounded-lg shadow-sm hover:shadow-md transition bg-gray-900 text-white">
            <span className={`text-xs font-bold px-2 py-1 rounded ${post.category === 'GAMES' ? 'bg-red-500' : 'bg-blue-500'}`}>
              {post.category}
            </span>
            <h2 className="text-2xl font-bold mt-2">{post.title}</h2>
            <p className="text-gray-400 mt-2 line-clamp-3">{post.content}</p>
            <a href={`/post/${post.slug}`} className="inline-block mt-4 text-blue-300 hover:underline">
              Ler mais →
            </a>
          </div>
        ))}
      </div>
    </main>
  );
}