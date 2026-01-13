import { NextResponse } from 'next/server';

export const runtime = 'edge'; // Obrigatório para Cloudflare

export async function POST(req: Request) {
  try {
    const { email, category } = await req.json();

    if (!email || !category) {
      return NextResponse.json({ error: 'Email e categoria são obrigatórios' }, { status: 400 });
    }

    // Decide qual lista usar com base na categoria
    const listId = category === 'GAMES' 
      ? Number(process.env.BREVO_LIST_ID_GAMES) 
      : Number(process.env.BREVO_LIST_ID_CYBER);

    // Manda para o Brevo
    const response = await fetch('https://api.brevo.com/v3/contacts', {
      method: 'POST',
      headers: {
        'api-key': process.env.BREVO_API_KEY!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        listIds: [listId],
        updateEnabled: true, // Se o contato já existir, só atualiza a lista
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Erro Brevo:', errorData);
      return NextResponse.json({ error: 'Erro ao salvar no Brevo' }, { status: 500 });
    }

    return NextResponse.json({ success: true });

  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 });
  }
}