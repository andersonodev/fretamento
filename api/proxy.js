// Proxy simples e robusto para Node.js 22 (fetch nativo)
module.exports = async (req, res) => {
  console.log(`[PROXY] ${req.method} ${req.url}`);
  
  // URL do Heroku
  const herokuUrl = 'https://fretamento-intertouring-d423e478ec7f.herokuapp.com';
  const targetUrl = `${herokuUrl}${req.url || '/'}`;
  
  console.log(`[PROXY] Target: ${targetUrl}`);
  
  try {
    // Headers básicos
    const headers = {
      'User-Agent': 'Vercel-Proxy/1.0'
    };
    
    // Fazer requisição usando fetch nativo
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      redirect: 'follow' // Seguir redirects
    });
    
    if (!response.ok) {
      console.log(`[PROXY] Error: ${response.status} ${response.statusText}`);
      return res.status(response.status).send(`Proxy Error: ${response.statusText}`);
    }
    
    // Obter conteúdo
    const content = await response.text();
    const contentType = response.headers.get('content-type') || 'text/html';
    
    // Configurar resposta
    res.setHeader('Content-Type', contentType);
    
    // Se for HTML, substituir URLs do Heroku pela Vercel
    if (contentType.includes('text/html')) {
      const modifiedContent = content.replace(
        /https:\/\/fretamento-intertouring-d423e478ec7f\.herokuapp\.com/g,
        'https://fretamentointertouring.vercel.app'
      );
      res.send(modifiedContent);
    } else {
      res.send(content);
    }
    
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