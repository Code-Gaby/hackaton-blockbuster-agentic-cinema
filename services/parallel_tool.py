import os
import json
import logging
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logger = logging.getLogger('ParallelSearchTool')

class ParallelSearchTool:
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except Exception:
                pass
        self.api_key = api_key or os.getenv('PARALLEL_API_KEY')
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from parallel import Parallel
                self.client = Parallel(api_key=self.api_key)
            except Exception as e:
                logger.warning(f'No se pudo instanciar Parallel SDK: {e}. Se usara fallback HTTP.')
                self.client = None

    def is_configured(self) -> bool:
        key = self.api_key or os.getenv('PARALLEL_API_KEY')
        return bool(key and key.strip() and not key.startswith('your_parallel_api_key'))

    def search(
        self,
        objective: str,
        search_queries: Optional[List[str]] = None,
        mode: str = 'fast',
        max_results: int = 5
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                'success': False,
                'error': 'PARALLEL_API_KEY_NOT_FOUND',
                'message': 'La clave de API de Parallel (PARALLEL_API_KEY) no esta configurada en .env.',
                'objective': objective,
                'search_queries': search_queries or [],
                'results': [],
                'results_count': 0
            }

        api_key = self.api_key or os.getenv('PARALLEL_API_KEY')
        queries = search_queries if search_queries and len(search_queries) > 0 else [objective[:100]]

        if self.client:
            try:
                resp = self.client.search(
                    objective=objective,
                    search_queries=queries,
                    mode=mode
                )
                raw_results = getattr(resp, 'results', []) or []
                normalized = []
                for item in raw_results[:max_results]:
                    title = getattr(item, 'title', '') or 'Sin titulo'
                    url = getattr(item, 'url', '') or ''
                    publish_date = getattr(item, 'publish_date', None)
                    raw_excerpts = getattr(item, 'excerpts', []) or []
                    excerpts = [str(e).strip() for e in raw_excerpts if str(e).strip()]
                    normalized.append({
                        'title': title,
                        'url': url,
                        'publish_date': publish_date,
                        'excerpts': excerpts[:3]
                    })

                return {
                    'success': True,
                    'objective': objective,
                    'search_queries': queries,
                    'results_count': len(normalized),
                    'results': normalized,
                    'provider': 'parallel_sdk'
                }
            except Exception as sdk_err:
                logger.warning(f'Falla en llamada SDK de Parallel: {sdk_err}. Intentando fallback HTTP.')

        try:
            url = 'https://api.parallel.ai/v1/search'
            payload = {
                'objective': objective,
                'search_queries': queries,
                'mode': mode
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'User-Agent': 'AgenticCinema-DirectorAgent/1.0'
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                raw_results = data.get('results', []) or []
                normalized = []
                for item in raw_results[:max_results]:
                    normalized.append({
                        'title': item.get('title') or 'Sin titulo',
                        'url': item.get('url') or '',
                        'publish_date': item.get('publish_date'),
                        'excerpts': item.get('excerpts', [])[:3]
                    })

                return {
                    'success': True,
                    'objective': objective,
                    'search_queries': queries,
                    'results_count': len(normalized),
                    'results': normalized,
                    'provider': 'parallel_http_fallback'
                }
        except urllib.error.HTTPError as he:
            return {
                'success': False,
                'error': f'HTTP_{he.code}',
                'message': f'Parallel Search API devolvio error {he.code}.',
                'objective': objective,
                'search_queries': queries,
                'results': [],
                'results_count': 0
            }
        except Exception as net_err:
            return {
                'success': False,
                'error': 'NETWORK_ERROR',
                'message': f'Error de red al conectar con Parallel Search: {str(net_err)}',
                'objective': objective,
                'search_queries': queries,
                'results': [],
                'results_count': 0
            }
