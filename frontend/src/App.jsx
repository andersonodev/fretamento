import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import PropTypes from 'prop-types';
import PhotoAlbum from 'react-photo-album';
import Lightbox from 'yet-another-react-lightbox';
import 'yet-another-react-lightbox/styles.css';
import {
  FiPhone,
  FiMail,
  FiInstagram,
  FiHeart,
  FiGift,
  FiUsers,
  FiFeather,
  FiSun,
} from 'react-icons/fi';
import emailjs from '@emailjs/browser';

const navLinks = [
  { label: 'Início', id: 'inicio' },
  { label: 'Sobre', id: 'sobre' },
  { label: 'Eventos', id: 'eventos' },
  { label: 'Galeria', id: 'galeria' },
  { label: 'Depoimentos', id: 'depoimentos' },
  { label: 'Localização', id: 'localizacao' },
  { label: 'Contato', id: 'contato' },
];

const eventTypes = [
  {
    title: 'Casamentos',
    description:
      'Cenários ao ar livre, gazebo intimista e salão integrado para celebrar o amor com sofisticação e natureza.',
    icon: FiHeart,
  },
  {
    title: 'Aniversários',
    description:
      'Produções afetivas para todas as idades, com estrutura completa para festas diurnas ou noturnas.',
    icon: FiGift,
  },
  {
    title: 'Corporativos',
    description:
      'Workshops, ativações, confraternizações e imersões com ambientes versáteis e internet de alta velocidade.',
    icon: FiUsers,
  },
  {
    title: 'Retiros & Bem-estar',
    description:
      'Programação personalizada para retiros espirituais, encontros criativos e experiências de autocuidado.',
    icon: FiFeather,
  },
  {
    title: 'Mini Weddings',
    description:
      'Celebrações intimistas com gastronomia autoral, jardim iluminado e suíte exclusiva para os noivos.',
    icon: FiSun,
  },
];

const testimonials = [
  {
    quote:
      'O sítio foi o cenário perfeito para o nosso casamento. Equipe acolhedora e cada detalhe pensado com carinho.',
    name: 'Mariana & Lucas',
  },
  {
    quote:
      'Organizamos um retiro corporativo e saímos renovados. A natureza inspira e a infraestrutura impressiona.',
    name: 'Rafael Pereira • CEO, Nativa Tech',
  },
  {
    quote:
      'Meu aniversário de 50 anos foi mágico! Luzes, aromas e sabores criaram um ambiente inesquecível.',
    name: 'Patrícia Barra',
  },
];

const heroBackgroundImage =
  'https://images.unsplash.com/photo-1529636798458-92182e662485?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=samantha-gades-x40Q9jrEVT0-unsplash.jpg&w=2000';

const aboutImages = {
  primary:
    'https://images.unsplash.com/photo-1520854221256-17451cc331bf?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=jeremy-wong-weddings-464ps_nOflw-unsplash.jpg&w=2000',
  secondary:
    'https://images.unsplash.com/photo-1515934751635-c81c6bc9a2d8?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=beatriz-perez-moya-M2T1j-6Fn8w-unsplash.jpg&w=2000',
  tertiary:
    'https://images.unsplash.com/photo-1460978812857-470ed1c77af0?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=hisu-lee-FTW8ADj5igs-unsplash.jpg&w=2000',
};

const galleryPhotos = [
  {
    src: 'https://images.unsplash.com/photo-1520854221256-17451cc331bf?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=jeremy-wong-weddings-464ps_nOflw-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Enlace sob os ipês',
  },
  {
    src: 'https://images.unsplash.com/photo-1515934751635-c81c6bc9a2d8?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=beatriz-perez-moya-M2T1j-6Fn8w-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Produção da noiva na suíte jardim',
  },
  {
    src: 'https://images.unsplash.com/photo-1519741497674-611481863552?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=nathan-dumlao-5BB_atDT4oA-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Banquete com iluminação cênica',
  },
  {
    src: 'https://images.unsplash.com/photo-1606800052052-a08af7148866?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=sandy-millar-8vaQKYnawHw-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Pista de dança à luz de fairy lights',
  },
  {
    src: 'https://images.unsplash.com/photo-1523438885200-e635ba2c371e?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=jeremy-wong-weddings-K8KiCHh4WU4-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Cerimônia ao ar livre',
  },
  {
    src: 'https://images.unsplash.com/photo-1756143059109-76b40d384dba?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=samsung-memory-us-q6YYsP-mDYM-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Lounge no jardim ao entardecer',
  },
  {
    src: 'https://images.unsplash.com/photo-1545232979-8bf68ee9b1af?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=alvin-mahmudov-9_XfcBxf_uo-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Jantar sob as estrelas',
  },
  {
    src: 'https://images.unsplash.com/photo-1606216794074-735e91aa2c92?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=jakob-owens-SiniLJkXhMc-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Portal de flores para dizer sim',
  },
  {
    src: 'https://images.unsplash.com/photo-1756143058430-c71365889d82?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=samsung-memory-us-1MG93MGhe_8-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Golden hour no espelho d’água',
  },
  {
    src: 'https://images.unsplash.com/photo-1606800052052-a08af7148866?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=sandy-millar-8vaQKYnawHw-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Detalhes florais com luz ambiente',
  },
  {
    src: 'https://images.unsplash.com/photo-1502635385003-ee1e6a1a742d?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=evelina-friman-hw_sKmjb0ns-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Recepção no jardim com folhagens',
  },
  {
    src: 'https://images.unsplash.com/photo-1756143058493-2d14887e41e6?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=samsung-memory-us-8q_3BQW4RXo-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Abraço dos noivos ao pôr do sol',
  },
  {
    src: 'https://images.unsplash.com/photo-1460978812857-470ed1c77af0?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=hisu-lee-FTW8ADj5igs-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Cordão de luzes sobre o lounge externo',
  },
  {
    src: 'https://images.unsplash.com/photo-1529636798458-92182e662485?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=samantha-gades-x40Q9jrEVT0-unsplash.jpg&w=2000',
    width: 2000,
    height: 1333,
    title: 'Trilha iluminada rumo à celebração',
  },
];

const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const SectionTitle = ({ eyebrow, title, description }) => (
  <motion.div
    initial="hidden"
    whileInView="visible"
    viewport={{ once: true, amount: 0.4 }}
    className="max-w-2xl mx-auto text-center mb-14"
  >
    <motion.p
      variants={fadeInUp}
      className="text-sm uppercase tracking-[0.35em] text-accent-sage/80 mb-4"
    >
      {eyebrow}
    </motion.p>
    <motion.h2
      variants={fadeInUp}
      className="text-3xl md:text-4xl font-serif text-ink/90 mb-6"
    >
      {title}
    </motion.h2>
    {description && (
      <motion.p
        variants={fadeInUp}
        className="text-base md:text-lg text-ink/70 leading-relaxed"
      >
        {description}
      </motion.p>
    )}
  </motion.div>
);

SectionTitle.propTypes = {
  eyebrow: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
};

function App() {
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [lightboxIndex, setLightboxIndex] = useState(-1);
  const [formStatus, setFormStatus] = useState('idle');
  const formRef = useRef(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 7000);
    return () => clearInterval(interval);
  }, []);

  const handleNavClick = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const photos = useMemo(() => galleryPhotos, []);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!formRef.current) return;

    setFormStatus('sending');
    const serviceId = import.meta.env.VITE_EMAILJS_SERVICE_ID;
    const templateId = import.meta.env.VITE_EMAILJS_TEMPLATE_ID;
    const publicKey = import.meta.env.VITE_EMAILJS_PUBLIC_KEY;

    if (!serviceId || !templateId || !publicKey) {
      console.warn('Configure as variáveis do EmailJS para habilitar o envio do formulário.');
      setFormStatus('error');
      return;
    }

    emailjs
      .sendForm(
        serviceId,
        templateId,
        formRef.current,
        publicKey
      )
      .then(() => {
        setFormStatus('success');
        formRef.current?.reset();
      })
      .catch(() => {
        setFormStatus('error');
      });
  };

  return (
    <div className="bg-background text-ink">
      <header className="fixed top-0 inset-x-0 z-50 bg-background/80 backdrop-blur-xl border-b border-accent-sand/40">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0, transition: { duration: 0.6 } }}
            className="flex flex-col text-sm uppercase tracking-[0.3em] text-ink/80"
          >
            <span className="font-serif text-xl tracking-normal text-ink">Sítio Horizonte Verde</span>
            <span className="text-xs text-ink/60">Natureza • Elegância • Experiências</span>
          </motion.div>
          <div className="hidden md:flex items-center gap-8 text-sm">
            {navLinks.map((link) => (
              <button
                key={link.id}
                onClick={() => handleNavClick(link.id)}
                className="uppercase tracking-[0.3em] text-ink/60 hover:text-ink transition"
              >
                {link.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => handleNavClick('contato')}
            className="hidden md:inline-flex items-center rounded-full bg-accent-sage/90 px-5 py-2 text-sm uppercase tracking-[0.3em] text-background shadow-soft transition hover:bg-accent-sage"
          >
            Agendar visita
          </button>
        </nav>
      </header>

      <main className="pt-20">
        <section
          id="inicio"
          className="relative min-h-[90vh] flex items-center overflow-hidden"
        >
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `linear-gradient(120deg, rgba(250,249,246,0.75), rgba(250,249,246,0.3)), url(${heroBackgroundImage})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/20 via-background/60 to-background" />
          <div className="relative mx-auto flex w-full max-w-6xl flex-col items-start gap-10 px-5 py-24 md:py-32">
            <motion.span
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0, transition: { duration: 0.8 } }}
              className="rounded-full bg-background/70 px-4 py-2 text-xs uppercase tracking-[0.35em] text-ink/70 shadow-soft backdrop-blur"
            >
              Um refúgio de encontros memoráveis
            </motion.span>
            <motion.h1
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0, transition: { duration: 0.9, delay: 0.1 } }}
              className="max-w-3xl font-serif text-4xl leading-tight text-ink md:text-6xl"
            >
              Celebre momentos inesquecíveis em meio à natureza
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0, transition: { duration: 0.9, delay: 0.2 } }}
              className="max-w-xl text-base text-ink/70 md:text-lg"
            >
              Um sítio boutique na região de Vargem Grande, RJ, com espaços versáteis para casamentos, aniversários, eventos corporativos e retiros que pedem calma, sofisticação e conexão com a natureza.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0, transition: { duration: 0.9, delay: 0.3 } }}
              className="flex flex-col gap-4 sm:flex-row"
            >
              <button
                onClick={() => handleNavClick('contato')}
                className="inline-flex items-center justify-center rounded-full bg-accent-sage px-8 py-3 text-sm uppercase tracking-[0.3em] text-background shadow-soft transition hover:bg-accent-sage/90"
              >
                Agende sua visita
              </button>
              <button
                onClick={() => handleNavClick('galeria')}
                className="inline-flex items-center justify-center rounded-full border border-accent-sand/60 bg-background/70 px-8 py-3 text-sm uppercase tracking-[0.3em] text-ink/70 transition hover:border-accent-sage hover:text-ink"
              >
                Conheça o espaço
              </button>
            </motion.div>
          </div>
        </section>

        <section id="sobre" className="relative overflow-hidden py-24">
          <div className="absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-accent-sand/20 to-transparent" />
          <div className="relative mx-auto grid max-w-6xl gap-14 px-5 md:grid-cols-2 md:items-center">
            <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }} variants={fadeInUp}>
              <p className="text-sm uppercase tracking-[0.35em] text-accent-sage/80">Sobre nós</p>
              <h2 className="mt-4 font-serif text-3xl text-ink md:text-4xl">
                Um jardim contemporâneo, pensado para viver histórias com calma
              </h2>
              <p className="mt-6 text-base text-ink/70 md:text-lg">
                Inspirado em refúgios praianos, o Sítio Horizonte Verde combina arquitetura fluida, ambientes integrados e paisagismo tropical. Cada celebração recebe curadoria exclusiva de fornecedores parceiros, estrutura para até 250 convidados, suíte para produção dos anfitriões e áreas técnicas que garantem eventos impecáveis.
              </p>
              <div className="mt-8 grid gap-6 sm:grid-cols-2">
                {["Deck panorâmico com vista para a mata", "Orquidário iluminado e lago natural", "Gastronomia autoral com cozinha equipada", "Equipe especializada em experiências sob medida"].map((item) => (
                  <div key={item} className="rounded-3xl border border-accent-sand/40 bg-background/80 p-5 shadow-sm backdrop-blur">
                    <p className="text-sm text-ink/80">{item}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            <div className="grid gap-6 sm:grid-cols-2">
              <motion.div
                className="group relative h-72 overflow-hidden rounded-3xl shadow-soft"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0, transition: { duration: 0.7 } }}
                viewport={{ once: true, amount: 0.3 }}
              >
                <img
                  src={aboutImages.primary}
                  alt="Produção da noiva ao ar livre"
                  className="h-full w-full object-cover transition duration-[4000ms] ease-out group-hover:scale-110"
                />
              </motion.div>
              <motion.div
                className="group relative h-60 overflow-hidden rounded-3xl border border-accent-sand/30 bg-background shadow-soft"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0, transition: { duration: 0.7, delay: 0.1 } }}
                viewport={{ once: true, amount: 0.3 }}
              >
                <img
                  src={aboutImages.secondary}
                  alt="Detalhes florais na mesa de doces"
                  className="h-full w-full object-cover transition duration-[4000ms] ease-out group-hover:scale-110"
                />
              </motion.div>
              <motion.div
                className="group relative h-48 overflow-hidden rounded-3xl shadow-soft md:col-span-2"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0, transition: { duration: 0.7, delay: 0.15 } }}
                viewport={{ once: true, amount: 0.3 }}
              >
                <img
                  src={aboutImages.tertiary}
                  alt="Pista de dança iluminada ao ar livre"
                  className="h-full w-full object-cover transition duration-[4000ms] ease-out group-hover:scale-110"
                />
              </motion.div>
            </div>
          </div>
        </section>

        <section id="eventos" className="bg-gradient-to-b from-background via-white/60 to-background py-24">
          <div className="mx-auto max-w-6xl px-5">
            <SectionTitle
              eyebrow="Eventos"
              title="Cenários versáteis para diferentes experiências"
              description="Ambientes integrados, iluminação cênica e equipe apaixonada por receber bem garantem uma atmosfera leve e memorável para cada evento."
            />
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {eventTypes.map(({ title, description, icon: Icon }) => (
                <motion.div
                  key={title}
                  variants={fadeInUp}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, amount: 0.2 }}
                  className="group flex flex-col rounded-3xl border border-accent-sand/40 bg-background/90 p-8 shadow-soft transition hover:-translate-y-1 hover:border-accent-sage/80 hover:bg-white/90"
                >
                  <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-full bg-accent-sand/40 text-accent-sage">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-serif text-2xl text-ink">{title}</h3>
                  <p className="mt-4 text-sm text-ink/70 md:text-base">{description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="galeria" className="py-24">
          <div className="mx-auto max-w-6xl px-5">
            <SectionTitle
              eyebrow="Galeria"
              title="Luz natural, paisagismo e detalhes afetivos"
              description="Confira alguns registros de celebrações recentes e inspire-se para compor o seu evento no Horizonte Verde."
            />
            <div className="rounded-3xl border border-accent-sand/40 bg-background/70 p-4 shadow-soft">
              <PhotoAlbum
                layout="rows"
                photos={photos}
                targetRowHeight={260}
                onClick={({ index }) => setLightboxIndex(index)}
              />
            </div>
            <Lightbox
              open={lightboxIndex >= 0}
              close={() => setLightboxIndex(-1)}
              index={lightboxIndex}
              slides={photos.map((photo) => ({ src: photo.src, description: photo.title }))}
            />
          </div>
        </section>

        <section id="depoimentos" className="bg-gradient-to-b from-background via-white/70 to-background py-24">
          <div className="mx-auto max-w-4xl px-5 text-center">
            <SectionTitle
              eyebrow="Depoimentos"
              title="Experiências que ecoam boas memórias"
              description="Histórias reais de anfitriões e convidados que viveram momentos especiais conosco."
            />
            <div className="relative overflow-hidden rounded-3xl border border-accent-sand/40 bg-background/90 p-10 shadow-soft">
              <AnimatePresence mode="wait" initial={false}>
                <AnimateTestimonial
                  key={testimonials[activeTestimonial].name}
                  testimonial={testimonials[activeTestimonial]}
                />
              </AnimatePresence>
              <div className="mt-10 flex justify-center gap-3">
                {testimonials.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveTestimonial(idx)}
                    className={`h-2 w-8 rounded-full transition ${
                      idx === activeTestimonial ? 'bg-accent-sage' : 'bg-accent-sand/60'
                    }`}
                    aria-label={`Ver depoimento ${idx + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="localizacao" className="py-24">
          <div className="mx-auto grid max-w-6xl gap-12 px-5 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeInUp}
              className="overflow-hidden rounded-3xl shadow-soft"
            >
              <iframe
                title="Mapa Sítio Horizonte Verde"
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3675.626319079693!2d-43.51578352408252!3d-22.89370177925917!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x9964ddcde94f1d%3A0x3f1eb04c0857a1be!2sVargem%20Grande%2C%20Rio%20de%20Janeiro%20-%20RJ!5e0!3m2!1spt-BR!2sbr!4v1700774112345!5m2!1spt-BR!2sbr"
                className="h-[320px] w-full border-0"
                allowFullScreen=""
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </motion.div>
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeInUp}
              className="space-y-6"
            >
              <p className="text-sm uppercase tracking-[0.35em] text-accent-sage/80">Como chegar</p>
              <h3 className="font-serif text-3xl text-ink">Entre a serra e o mar, em Vargem Grande - RJ</h3>
              <p className="text-base text-ink/70">
                A 35 minutos da Barra da Tijuca e cercado por reservas naturais, o sítio conta com estacionamento próprio, acesso pavimentado e estrutura para receptivo de fornecedores e convidados.
              </p>
              <div className="grid gap-4 text-sm text-ink/80">
                <div className="flex items-center gap-3">
                  <FiPhone className="h-5 w-5 text-accent-sage" />
                  <span>(21) 98143-0186</span>
                </div>
                <div className="flex items-center gap-3">
                  <FiMail className="h-5 w-5 text-accent-sage" />
                  <span>patriciabarra.decor@gmail.com</span>
                </div>
                <div className="flex items-center gap-3">
                  <FiInstagram className="h-5 w-5 text-accent-sage" />
                  <span>@sitiohorizonteverde</span>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <section id="contato" className="bg-gradient-to-b from-background via-white/60 to-background py-24">
          <div className="mx-auto max-w-5xl px-5">
            <SectionTitle
              eyebrow="Contato"
              title="Vamos desenhar o seu evento?"
              description="Preencha o formulário e retornaremos com proposta personalizada em até 24 horas."
            />
            <motion.form
              ref={formRef}
              onSubmit={handleSubmit}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              variants={fadeInUp}
              className="grid gap-6 rounded-3xl border border-accent-sand/40 bg-background/90 p-8 shadow-soft md:grid-cols-2"
            >
              <div className="flex flex-col gap-2">
                <label htmlFor="user_name" className="text-xs uppercase tracking-[0.3em] text-ink/60">
                  Nome completo
                </label>
                <input
                  id="user_name"
                  name="user_name"
                  type="text"
                  required
                  placeholder="Como podemos te chamar?"
                  className="rounded-2xl border border-accent-sand/50 bg-white/80 px-4 py-3 text-sm text-ink shadow-sm focus:border-accent-sage focus:outline-none"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label htmlFor="user_email" className="text-xs uppercase tracking-[0.3em] text-ink/60">
                  E-mail
                </label>
                <input
                  id="user_email"
                  name="user_email"
                  type="email"
                  required
                  placeholder="nome@email.com"
                  className="rounded-2xl border border-accent-sand/50 bg-white/80 px-4 py-3 text-sm text-ink shadow-sm focus:border-accent-sage focus:outline-none"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label htmlFor="event_type" className="text-xs uppercase tracking-[0.3em] text-ink/60">
                  Tipo de evento
                </label>
                <select
                  id="event_type"
                  name="event_type"
                  required
                  className="rounded-2xl border border-accent-sand/50 bg-white/80 px-4 py-3 text-sm text-ink shadow-sm focus:border-accent-sage focus:outline-none"
                >
                  <option value="">Selecione</option>
                  <option value="Casamento">Casamento</option>
                  <option value="Aniversário">Aniversário</option>
                  <option value="Corporativo">Corporativo</option>
                  <option value="Retiro">Retiro</option>
                  <option value="Outro">Outro</option>
                </select>
              </div>
              <div className="flex flex-col gap-2">
                <label htmlFor="event_date" className="text-xs uppercase tracking-[0.3em] text-ink/60">
                  Data prevista
                </label>
                <input
                  id="event_date"
                  name="event_date"
                  type="date"
                  className="rounded-2xl border border-accent-sand/50 bg-white/80 px-4 py-3 text-sm text-ink shadow-sm focus:border-accent-sage focus:outline-none"
                />
              </div>
              <div className="md:col-span-2 flex flex-col gap-2">
                <label htmlFor="message" className="text-xs uppercase tracking-[0.3em] text-ink/60">
                  Mensagem
                </label>
                <textarea
                  id="message"
                  name="message"
                  rows="5"
                  required
                  placeholder="Conte-nos mais sobre a sua celebração, quantidade de convidados e referências desejadas."
                  className="rounded-2xl border border-accent-sand/50 bg-white/80 px-4 py-3 text-sm text-ink shadow-sm focus:border-accent-sage focus:outline-none"
                />
              </div>
              <div className="md:col-span-2 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <p className="text-xs uppercase tracking-[0.25em] text-ink/50">
                  Responderemos em até 24 horas úteis.
                </p>
                <button
                  type="submit"
                  className="inline-flex items-center justify-center rounded-full bg-accent-sage px-10 py-3 text-sm uppercase tracking-[0.3em] text-background shadow-soft transition hover:bg-accent-sage/90 disabled:cursor-not-allowed disabled:bg-accent-sand/70"
                  disabled={formStatus === 'sending'}
                >
                  {formStatus === 'sending' ? 'Enviando...' : 'Enviar mensagem'}
                </button>
              </div>
              {formStatus === 'success' && (
                <p className="md:col-span-2 rounded-2xl bg-accent-sage/10 px-4 py-3 text-sm text-accent-sage">
                  Recebemos sua mensagem! Em breve nossa equipe entrará em contato.
                </p>
              )}
              {formStatus === 'error' && (
                <p className="md:col-span-2 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-500">
                  Não foi possível enviar sua mensagem agora. Por favor, tente novamente ou escreva para patriciabarra.decor@gmail.com.
                </p>
              )}
            </motion.form>
          </div>
        </section>
      </main>

      <footer className="border-t border-accent-sand/30 bg-background/90">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 py-10 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col">
            <span className="font-serif text-xl text-ink">Sítio Horizonte Verde</span>
            <span className="text-sm text-ink/60">Onde a natureza celebra junto com você.</span>
          </div>
          <div className="flex flex-col text-sm text-ink/70 md:text-right">
            <span>patriciabarra.decor@gmail.com</span>
            <span>(21) 98143-0186</span>
            <span>Vargem Grande • Rio de Janeiro - RJ</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

const AnimateTestimonial = ({ testimonial }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    animate={{ opacity: 1, y: 0, transition: { duration: 0.7 } }}
    exit={{ opacity: 0, y: -30, transition: { duration: 0.5 } }}
    className="flex flex-col items-center gap-6"
  >
    <p className="text-lg font-light leading-relaxed text-ink/80 md:text-xl">“{testimonial.quote}”</p>
    <span className="text-sm uppercase tracking-[0.3em] text-ink/60">{testimonial.name}</span>
  </motion.div>
);

AnimateTestimonial.propTypes = {
  testimonial: PropTypes.shape({
    quote: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
  }).isRequired,
};

export default App;
