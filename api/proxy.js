const https = require('https');
const http = require('http');
const { URL } = require('url');

module.exports = async (req, res) => {
  // URL do Heroku
  const herokuUrl = 'https://fretamento-intertouring-d423e478ec7f.herokuapp.com';
  
  // Construir a URL completa
  const targetUrl = `${herokuUrl}${req.url || '/'}`;
  
  try {
    // Preparar headers
    const forwardHeaders = { ...req.headers };
    delete forwardHeaders.host;
    delete forwardHeaders['x-forwarded-host'];
    delete forwardHeaders['x-forwarded-proto'];
    
    // Adicionar headers necessários
    forwardHeaders.host = 'fretamento-intertouring-d423e478ec7f.herokuapp.com';
    forwardHeaders['x-forwarded-for'] = req.headers['x-forwarded-for'] || req.ip || '';
    
    // Fazer fetch para o Heroku
    const response = await fetch(targetUrl, {
      method: req.method,
      headers: forwardHeaders,
      body: req.method !== 'GET' && req.method !== 'HEAD' ? JSON.stringify(req.body) : undefined,
    });
    
    // Copiar status
    res.status(response.status);
    
    // Copiar headers importantes
    const contentType = response.headers.get('content-type') || '';
    if (contentType) {
      res.setHeader('content-type', contentType);
    }
    
    // Processar conteúdo
    if (contentType.includes('text/html')) {
      let html = await response.text();
      
      // Substituir URLs do Heroku pela Vercel
      html = html.replace(
        /https:\/\/fretamento-intertouring-d423e478ec7f\.herokuapp\.com/g,
        'https://fretamentointertouring.vercel.app'
      );
      
      res.send(html);
    } else {
      // Para outros tipos, retornar direto
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
};