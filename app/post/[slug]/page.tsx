import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { notFound } from 'next/navigation';

export const runtime = 'edge';

export default async function Post({ params }: { params: Promise<{ slug: string }> }) {
  // No Next.js 15, precisamos aguardar os parametros da URL
  const { slug } = await params;

  // Busca o post no banco de dados que tenha esse slug
  const { data: post } = await supabase
    .from('posts')
    .select('*')
    .eq('slug', slug)
    .single();

  // Se não achar nada no banco, manda para a página 404 oficial
  if (!post) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-black text-white p-8 font-sans">
      <main className="max-w-3xl mx-auto mt-10">
        {/* Botão de Voltar */}
        <Link 
          href="/" 
          className="text-gray-400 hover:text-white transition-colors text-sm mb-8 inline-block"
        >
          ← Voltar para a Home
        </Link>

        {/* Cabeçalho do Post */}
        <header className="mb-10 border-b border-gray-800 pb-8">
          <span className="bg-blue-600 text-xs font-bold px-2 py-1 rounded text-white mb-4 inline-block">
            {post.category}
          </span>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
            {post.title}
          </h1>
          <time className="text-gray-500 text-sm">
            Postado em {new Date(post.created_at).toLocaleDateString('pt-BR')}
          </time>
        </header>

        {/* Conteúdo do Post */}
        <article className="prose prose-invert prose-lg max-w-none">
          {/* whitespace-pre-wrap faz o texto respeitar os parágrafos que a IA criou */}
          <div className="whitespace-pre-wrap leading-relaxed text-gray-300">
            {post.content}
          </div>
        </article>
      </main>
    </div>
  );
}