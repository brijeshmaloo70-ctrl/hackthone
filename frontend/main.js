/* ============================================================
   CareSync AI — Landing Page JS
   ============================================================ */

/* ── Navbar scroll effect ─────────────────────────────────── */
const nav = document.getElementById('nav');
if (nav) {
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });
}

/* ── Mobile burger menu ───────────────────────────────────── */
const burger   = document.getElementById('navBurger');
const mobileMenu = document.getElementById('navMobile');
if (burger && mobileMenu) {
  burger.addEventListener('click', () => {
    const open = mobileMenu.classList.toggle('open');
    burger.setAttribute('aria-expanded', open);
  });
  // Close on link click
  mobileMenu.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => mobileMenu.classList.remove('open'));
  });
}

/* ── Scroll reveal ────────────────────────────────────────── */
const revealObs = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // Stagger children of grids
        const delay = entry.target.dataset.delay
          ? parseInt(entry.target.dataset.delay)
          : 0;
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, delay);
        revealObs.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
);

// Stagger grid children
document.querySelectorAll('.features-grid, .agents-grid, .tech-grid, .impact-grid').forEach(grid => {
  grid.querySelectorAll('.reveal').forEach((el, i) => {
    el.dataset.delay = i * 80;
  });
});

document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

/* ── Active nav link highlighting ────────────────────────── */
const sections  = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav__links a');

const sectionObs = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        navLinks.forEach(a => {
          a.classList.toggle('active', a.getAttribute('href') === `#${id}`);
        });
      }
    });
  },
  { threshold: 0.35 }
);
sections.forEach(s => sectionObs.observe(s));

/* ── Hero vitals ticker ───────────────────────────────────── */
// Cycle through some simulated days to show the widget "live"
const tickerData = [
  { bp: '139/87', gluc: '185.5', hr: '73', adh: '95%', adh_warn: false },
  { bp: '146/88', gluc: '193.6', hr: '73', adh: '90%', adh_warn: false },
  { bp: '155/86', gluc: '212.6', hr: '81', adh: '75%', adh_warn: true  },
  { bp: '165/94', gluc: '275.6', hr: '77', adh: '65%', adh_warn: true  },
  { bp: '170/105', gluc: '322.4', hr: '80', adh: '52%', adh_warn: true },
  { bp: '162/97', gluc: '296.6', hr: '90', adh: '70%', adh_warn: true  },
];

let tickIdx = 0;
function tickVitals() {
  const d = tickerData[tickIdx % tickerData.length];
  const bpEl   = document.getElementById('wBP');
  const glucEl = document.getElementById('wGluc');
  const hrEl   = document.getElementById('wHR');
  const adhEl  = document.getElementById('wAdh');
  if (!bpEl) return;

  [bpEl, glucEl, hrEl, adhEl].forEach(el => el.classList.add('fade-update'));
  setTimeout(() => {
    bpEl.textContent   = d.bp;
    glucEl.textContent = d.gluc;
    hrEl.textContent   = d.hr;
    adhEl.textContent  = d.adh;
    adhEl.classList.toggle('warn', d.adh_warn);
    [bpEl, glucEl, hrEl, adhEl].forEach(el => el.classList.remove('fade-update'));
  }, 300);

  tickIdx++;
}

// Add CSS for fade-update
const fadeStyle = document.createElement('style');
fadeStyle.textContent = `
  .fade-update { opacity: 0.3 !important; transition: opacity 0.3s; }
  .nav__links a.active { color: var(--text) !important; }
`;
document.head.appendChild(fadeStyle);

setInterval(tickVitals, 3000);

/* ── Event bus items staggered animation ─────────────────── */
const busObs = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('.event-bus__event').forEach((el, i) => {
          el.style.animationDelay = `${i * 200}ms`;
        });
        busObs.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.3 }
);
const eventBus = document.querySelector('.event-bus');
if (eventBus) busObs.observe(eventBus);

/* ── Timeline entrance animation ─────────────────────────── */
document.querySelectorAll('.timeline__item').forEach((item, i) => {
  item.style.transitionDelay = `${i * 120}ms`;
});

/* ── Smooth scroll for anchor links ──────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

/* ── Stat cards counter animation ────────────────────────── */
function animateCounter(el, target, suffix = '', duration = 1200) {
  const isFloat = target % 1 !== 0;
  const start  = performance.now();
  const update = (now) => {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - t, 3); // ease-out-cubic
    const value = isFloat
      ? (ease * target).toFixed(1)
      : Math.round(ease * target);
    el.textContent = value + suffix;
    if (t < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

const counterObs = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const nums = entry.target.querySelectorAll('.impact-stat__num');
      nums.forEach(el => {
        const text = el.textContent.trim();
        // Parse number from text like "10+", "70%", "21", "3"
        const match = text.match(/^(\d+\.?\d*)(.*)/);
        if (match) {
          animateCounter(el, parseFloat(match[1]), match[2]);
        }
      });
      counterObs.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

const impactSection = document.querySelector('.impact-grid');
if (impactSection) counterObs.observe(impactSection);

/* ── Agent card hover glow ────────────────────────────────── */
document.querySelectorAll('.agent-card').forEach(card => {
  const agent = card.dataset.agent;
  const colors = { asha: '#4F8EF7', connect: '#10B981', medinsight: '#7C3AED' };
  const color = colors[agent] || '#4F8EF7';
  card.addEventListener('mouseenter', () => {
    card.style.boxShadow = `0 20px 60px ${color}25, 0 0 0 1px ${color}20`;
  });
  card.addEventListener('mouseleave', () => {
    card.style.boxShadow = '';
  });
});

/* ── Console Easter egg ───────────────────────────────────── */
console.log(
  '%c CareSync AI ',
  'background: linear-gradient(135deg,#4F8EF7,#7C3AED); color:#fff; font-size:18px; padding:8px 16px; border-radius:8px; font-weight:bold;',
  '\n\nProactive AI agents for chronic care and healthy ageing.\nTrack 4: Healthcare & Social Impact — HEALTH-01\nCodekshetra Hackathon'
);
