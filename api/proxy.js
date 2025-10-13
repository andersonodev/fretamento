// Proxy simples e robusto para Node.js 22 (fetch nativo)
module.exports = async (req, res) => {
  const startTime = Date.now();
  console.log(`[PROXY] ${req.method} ${req.url}`);
  
  // Prevenir loops: não fazer proxy de chamadas que já são do proxy
  if (req.url.startsWith('/api/')) {
    console.log('[PROXY] Ignoring API call to prevent loop');
    return res.status(404).send('Not Found');
  }
  
  // URL do Heroku
  const herokuUrl = 'https://fretamento-intertouring-d423e478ec7f.herokuapp.com';
  const targetUrl = `${herokuUrl}${req.url || '/'}`;
  
  console.log(`[PROXY] Target: ${targetUrl}`);
  
  try {
    // Headers básicos
    const headers = {
      'User-Agent': 'Vercel-Proxy/1.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    };
    
    // Criar controller para timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000); // 25 segundos
    
    // Fazer requisição usando fetch nativo
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      redirect: 'follow', // Seguir redirects
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      console.log(`[PROXY] Error: ${response.status} ${response.statusText}`);
      return res.status(response.status).send(`Proxy Error: ${response.statusText}`);
    }
    
    // Obter conteúdo
    const content = await response.text();
    const contentType = response.headers.get('content-type') || 'text/html';
    
    // Configurar resposta
    res.setHeader('Content-Type', contentType);
    
    // Log de performance
    const duration = Date.now() - startTime;
    console.log(`[PROXY] Response received in ${duration}ms`);
    
    // Se for HTML, substituir URLs do Heroku pela Vercel
    if (contentType.includes('text/html')) {
      const modifiedContent = content.replace(
        /https:\/\/fretamento-intertouring-d423e478ec7f\.herokuapp\.com/g,
        'https://fretamentointertouring.vercel.app'
      );
      console.log(`[PROXY] HTML modified, sending response (${modifiedContent.length} bytes)`);
      res.send(modifiedContent);
    } else {
      console.log(`[PROXY] Non-HTML content, sending response (${content.length} bytes)`);
      res.send(content);
    }
    
  } catch (error) {
    console.error('[PROXY] Error:', error.message);
    console.error('[PROXY] Stack:', error.stack);
    
    // Se for timeout, retornar mensagem específica
    if (error.name === 'AbortError') {
      return res.status(504).send(`
        <html>
          <head><title>Timeout</title></head>
          <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>⏱️ Timeout</h1>
            <p>O servidor demorou muito para responder.</p>
            <p><a href="/">Tentar novamente</a></p>
            <hr>
            <small>Target: ${targetUrl}</small>
          </body>
        </html>
      `);
    }
    
    return res.status(500).json({
      error: 'Proxy Error',
      message: error.message,
      target: targetUrl,
      timestamp: new Date().toISOString()
    });
  }
};