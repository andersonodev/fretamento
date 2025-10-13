const fetch = require('node-fetch').default;

module.exports = async (req, res) => {
  console.log(`[PROXY] ${req.method} ${req.url}`);
  
  // URL do Heroku - CORRIJA AQUI se necessário
  const herokuUrl = 'https://fretamento-intertouring-d423e478ec7f.herokuapp.com';
  
  // Construir URL completa
  const targetUrl = `${herokuUrl}${req.url || '/'}`;
  console.log(`[PROXY] Target: ${targetUrl}`);
  
  try {
    // Headers limpos
    const headers = {
      'User-Agent': req.headers['user-agent'] || 'Vercel-Proxy/1.0',
      'Accept': req.headers.accept || '*/*',
      'Accept-Language': req.headers['accept-language'] || 'pt-BR,pt;q=0.9,en;q=0.8',
      'Cache-Control': 'no-cache',
    };
    
    // Para POST/PUT, adicionar content-type se houver body
    if (req.body && req.method !== 'GET') {
      headers['Content-Type'] = 'application/json';
    }
    
    console.log(`[PROXY] Headers:`, Object.keys(headers));
    
    // Fazer requisição
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: req.body && req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
      redirect: 'manual', // Não seguir redirects automáticos
      timeout: 30000, // 30 segundos
    });
    
    console.log(`[PROXY] Response: ${response.status} ${response.statusText}`);
    
    // Headers de resposta
    const contentType = response.headers.get('content-type') || 'text/plain';
    const location = response.headers.get('location');
    
    // Se for redirect, ajustar location
    if (response.status >= 300 && response.status < 400 && location) {
      let newLocation = location;
      
      // Se o redirect for para o próprio Heroku, trocar pela Vercel
      if (location.startsWith('https://fretamento-intertouring-d423e478ec7f.herokuapp.com')) {
        newLocation = location.replace(
          'https://fretamento-intertouring-d423e478ec7f.herokuapp.com',
          'https://fretamentointertouring.vercel.app'
        );
      } else if (location.startsWith('/')) {
        // Redirect relativo
        newLocation = location;
      }
      
      console.log(`[PROXY] Redirect: ${location} -> ${newLocation}`);
      return res.redirect(response.status, newLocation);
    }
    
    // Configurar headers de resposta
    res.status(response.status);
    res.setHeader('Content-Type', contentType);
    
    // Obter conteúdo
    const content = await response.text();
    
    // Se for HTML, substituir URLs
    if (contentType.includes('text/html')) {
      const modifiedContent = content.replace(
        /https:\/\/fretamento-intertouring-d423e478ec7f\.herokuapp\.com/g,
        'https://fretamentointertouring.vercel.app'
      );
      return res.send(modifiedContent);
    }
    
    // Para outros tipos, enviar direto
    return res.send(content);
    
  } catch (error) {
    console.error('[PROXY] Error:', error.message);
    console.error('[PROXY] Stack:', error.stack);
    
    return res.status(500).json({
      error: 'Proxy Error',
      message: error.message,
      target: targetUrl,
      timestamp: new Date().toISOString()
    });
  }
};