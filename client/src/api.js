export async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'same-origin', cache: 'no-store', ...options,
    headers: { Accept: 'application/json', ...options.headers },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(data?.error || (response.status === 401 ? 'ログインが必要です。画面を再読み込みしてください。' : '読み込み・保存に失敗しました。'));
    error.status = response.status;
    throw error;
  }
  if (!data) throw new Error('API の応答を読み取れませんでした。');
  return data;
}

export function teamPrefix(route) { return '/t/' + encodeURIComponent(route.params.teamSlug); }
export function screenApi(route) { return teamPrefix(route) + '/api/screens' + route.path.replace(/^\/t\/[^/]+/, '') + (route.fullPath.includes('?') ? route.fullPath.slice(route.fullPath.indexOf('?')).split('#')[0] : ''); }
export function staticImage(path) { return '/static/' + String(path || 'default.png').split('/').map(encodeURIComponent).join('/'); }
