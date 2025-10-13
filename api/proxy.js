export default async function handler(req, res) {
  const { url, method, headers, body } = req;
  
  // URL do Heroku
  const herokuUrl = 'https://fretamento-intertouring-d423e478ec7f.herokuapp.com';
  
  // Construir a URL completa para o Heroku
  const targetUrl = `${herokuUrl}${url}`;
  
  try {
    // Preparar headers (remover headers problemáticos)
    const forwardHeaders = { ...headers };
    delete forwardHeaders.host;
    delete forwardHeaders['x-forwarded-host'];
    delete forwardHeaders['x-forwarded-proto'];
    
    // Adicionar headers necessários
    forwardHeaders['host'] = 'fretamento-intertouring-d423e478ec7f.herokuapp.com';
    forwardHeaders['x-forwarded-for'] = req.headers['x-forwarded-for'] || req.ip;
    
    // Configurar a requisição
    const fetchOptions = {
      method,
      headers: forwardHeaders,
    };
    
    // Adicionar body para métodos POST/PUT/PATCH
    if (method !== 'GET' && method !== 'HEAD' && body) {
      fetchOptions.body = JSON.stringify(body);
    }
    
    // Fazer a requisição para o Heroku
    const response = await fetch(targetUrl, fetchOptions);
    
    // Copiar headers da resposta (filtrar alguns)
    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      // Não copiar headers que podem causar problemas
      if (![
        'content-encoding', 
        'content-length', 
        'transfer-encoding',
        'connection',
        'upgrade',
        'strict-transport-security'
      ].includes(key.toLowerCase())) {
        responseHeaders[key] = value;
      }
    });
    
    // Definir headers da resposta
    Object.entries(responseHeaders).forEach(([key, value]) => {
      res.setHeader(key, value);
    });
    
    // Definir status code
    res.status(response.status);
    
    // Obter o conteúdo da resposta
    const contentType = response.headers.get('content-type') || '';
    
    if (contentType.includes('text/html')) {
      // Para HTML, substituir URLs do Heroku pela Vercel
      let html = await response.text();
      
      // Substituir URLs absolutas do Heroku
      html = html.replace(
        /https:\/\/fretamento-intertouring-d423e478ec7f\.herokuapp\.com/g,
        'https://fretamentointertouring.vercel.app'
      );
      
      // Substituir URLs relativas que podem estar apontando para o Heroku
      html = html.replace(
        /href="\/([^"]*?)"/g,
        'href="/$1"'
      );
      
      html = html.replace(
        /src="\/([^"]*?)"/g,
        'src="/$1"'
      );
      
      res.send(html);
    } else if (contentType.includes('application/json')) {
      // Para JSON, retornar como está
      const json = await response.json();
      res.json(json);
    } else {
      // Para outros tipos (CSS, JS, imagens), retornar como buffer
      const buffer = await response.arrayBuffer();
      res.send(Buffer.from(buffer));
    }
    
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(500).json({ 
      error: 'Proxy error', 
      message: error.message 
    });
  }
}