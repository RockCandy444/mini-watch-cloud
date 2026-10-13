export const runtime = 'nodejs';
export async function POST(request) {
  const base = process.env.MONITOR_API_URL;
  if (!base) return Response.json({error: 'MONITOR_API_URL을 설정해 주세요.'}, {status: 503});
  try {
    const headers = new Headers({'Content-Type': 'application/json'});
    const origin = request.headers.get('origin');
    if (origin) headers.set('Origin', origin);
    const upstream = await fetch(new URL('/general-api/auth/register', base), {
      method: 'POST', headers, body: await request.arrayBuffer(),
      cache: 'no-store', redirect: 'manual', signal: AbortSignal.timeout(15000),
    });
    return new Response(await upstream.arrayBuffer(), {
      status: upstream.status, headers: {'Content-Type': 'application/json', 'Cache-Control': 'no-store'},
    });
  } catch {
    return Response.json({error: '감시 API에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.'}, {status: 502});
  }
}
