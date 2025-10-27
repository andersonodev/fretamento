# Sítio Horizonte Verde – Landing Page

Aplicação desenvolvida em React + Vite com Tailwind CSS e Framer Motion para apresentar o Sítio Horizonte Verde, um espaço para eventos em Vargem Grande (RJ).

## Tecnologias principais

- [Vite](https://vitejs.dev/) com React 18
- [Tailwind CSS](https://tailwindcss.com/) para o design minimalista off-white
- [Framer Motion](https://www.framer.com/motion/) para animações suaves
- [React Photo Album](https://react-photo-album.com/) + [Yet Another React Lightbox](https://yet-another-react-lightbox.com/) para a galeria responsiva
- [EmailJS](https://www.emailjs.com/) para envio do formulário de contato

## Como rodar localmente

```bash
cd frontend
npm install
npm run dev
```

A aplicação ficará disponível em `http://localhost:5173`.

Para gerar os arquivos de produção utilize `npm run build`.

## Configuração do EmailJS

Crie um arquivo `.env` na pasta `frontend` com as variáveis presentes em `.env.example`:

```
VITE_EMAILJS_SERVICE_ID=seu_service_id
VITE_EMAILJS_TEMPLATE_ID=seu_template_id
VITE_EMAILJS_PUBLIC_KEY=sua_public_key
```

Sem esses valores o formulário exibirá uma mensagem de erro ao tentar enviar.

## Imagens

Para manter o repositório leve e sem binários, toda a galeria utiliza imagens hospedadas em bancos públicos (Unsplash e Pexels) referenciadas diretamente nas URLs configuradas no array `galleryPhotos` em `src/App.jsx`. Caso prefira usar arquivos locais, crie a pasta `frontend/public/imagens`, adicione as fotos desejadas (que permanecerão ignoradas pelo Git) e ajuste os caminhos nesse array.
