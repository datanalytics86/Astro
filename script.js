const zodiacRanges = [
  { sign: "Acuario", start: [1, 20], end: [2, 18], trait: "Mente innovadora y fuerte sentido de independencia." },
  { sign: "Piscis", start: [2, 19], end: [3, 20], trait: "Intuición alta y gran sensibilidad emocional." },
  { sign: "Aries", start: [3, 21], end: [4, 19], trait: "Impulso, valentía y tendencia al liderazgo." },
  { sign: "Tauro", start: [4, 20], end: [5, 20], trait: "Perseverancia, estabilidad y gusto por la seguridad." },
  { sign: "Géminis", start: [5, 21], end: [6, 20], trait: "Curiosidad, versatilidad y rapidez mental." },
  { sign: "Cáncer", start: [6, 21], end: [7, 22], trait: "Empatía, protección y fuerte conexión afectiva." },
  { sign: "Leo", start: [7, 23], end: [8, 22], trait: "Carisma, creatividad y necesidad de expresarse." },
  { sign: "Virgo", start: [8, 23], end: [9, 22], trait: "Análisis, orden y atención al detalle." },
  { sign: "Libra", start: [9, 23], end: [10, 22], trait: "Búsqueda de equilibrio, diplomacia y armonía." },
  { sign: "Escorpio", start: [10, 23], end: [11, 21], trait: "Intensidad, estrategia y profundidad emocional." },
  { sign: "Sagitario", start: [11, 22], end: [12, 21], trait: "Visión amplia, optimismo y amor por explorar." },
  { sign: "Capricornio", start: [12, 22], end: [1, 19], trait: "Disciplina, responsabilidad y ambición sostenida." },
];

const topicOrder = ["dinero", "finanzas", "amor", "trabajo"];

const topicsBySign = {
  Aries: {
    dinero: "Tiendes a tomar riesgos. Gana ventaja cuando defines un límite claro de gasto.",
    finanzas: "Te funciona una estrategia activa: metas trimestrales y revisión semanal.",
    amor: "Directo y apasionado. Te va mejor con comunicación honesta desde el inicio.",
    trabajo: "Brillas al liderar proyectos rápidos y con objetivos desafiantes.",
  },
  Tauro: {
    dinero: "Tienes facilidad para conservar recursos y construir estabilidad.",
    finanzas: "Invierte a largo plazo y evita decisiones por impulso.",
    amor: "Leal y constante. Necesitas seguridad y acuerdos claros.",
    trabajo: "Rindes más en ambientes estables con procesos definidos.",
  },
  Géminis: {
    dinero: "Tu creatividad abre oportunidades; evita dispersarte en demasiadas ideas.",
    finanzas: "Lleva un control simple pero diario para sostener foco.",
    amor: "Necesitas conversación y dinamismo para mantener conexión.",
    trabajo: "Destacas en comunicación, ventas, enseñanza y tareas variadas.",
  },
  Cáncer: {
    dinero: "Tu intuición para proteger recursos es fuerte; evita cargar gastos ajenos.",
    finanzas: "Presupuestos familiares y fondo de seguridad te favorecen.",
    amor: "Profundo y protector. Clave: expresar necesidades sin suponer.",
    trabajo: "Sobresales en equipos humanos y roles de cuidado/gestión cercana.",
  },
  Leo: {
    dinero: "Generas valor cuando confías en tus talentos visibles.",
    finanzas: "Prioriza ahorro automático antes de gastos de imagen.",
    amor: "Romántico y generoso. Te va bien con reconocimiento mutuo.",
    trabajo: "Liderazgo natural en escenarios creativos o de alto impacto.",
  },
  Virgo: {
    dinero: "Buen ojo para optimizar recursos y detectar fugas de gasto.",
    finanzas: "Plan detallado y métricas mensuales maximizan tus resultados.",
    amor: "Demuestras amor con hechos. Evita la autocrítica excesiva.",
    trabajo: "Excelente desempeño en análisis, salud, operaciones y calidad.",
  },
  Libra: {
    dinero: "Prosperas en alianzas y acuerdos equilibrados.",
    finanzas: "Diversifica y evita postergar decisiones por querer perfección.",
    amor: "Buscas armonía y cooperación; poner límites también es amor.",
    trabajo: "Fuerte en negociación, relaciones públicas y diseño.",
  },
  Escorpio: {
    dinero: "Estratega natural para mover recursos con visión.",
    finanzas: "Te favorecen planes de inversión profundos y de mediano plazo.",
    amor: "Intenso y leal. Confianza y transparencia son esenciales.",
    trabajo: "Brillas en investigación, psicología, datos y toma de decisiones complejas.",
  },
  Sagitario: {
    dinero: "Atraes oportunidades al expandir tu red y conocimientos.",
    finanzas: "Evita excesos optimistas: define topes y objetivos concretos.",
    amor: "Valoras libertad y aventura; necesitas acuerdos flexibles.",
    trabajo: "Excelente en docencia, viajes, contenido y visión estratégica.",
  },
  Capricornio: {
    dinero: "Gran capacidad para construir patrimonio con disciplina.",
    finanzas: "Tu mejor ventaja: constancia y horizonte de largo plazo.",
    amor: "Comprometido y serio. Expresar emociones fortalece el vínculo.",
    trabajo: "Rendimiento alto en gestión, dirección y metas exigentes.",
  },
  Acuario: {
    dinero: "Ingresos ligados a ideas innovadoras y proyectos no tradicionales.",
    finanzas: "Combina creatividad con estructura para evitar altibajos.",
    amor: "Necesitas conexión mental y espacio personal.",
    trabajo: "Destacas en tecnología, comunidad e innovación social.",
  },
  Piscis: {
    dinero: "Tu intuición ayuda, pero necesitas sistema para sostener resultados.",
    finanzas: "Automatizar ahorro te protege de decisiones emocionales.",
    amor: "Muy sensible y romántico; te beneficia una comunicación clara.",
    trabajo: "Fuerte en áreas creativas, terapéuticas y de apoyo humano.",
  },
};

const seasonalEnergies = [
  "etapa de expansión y oportunidades",
  "etapa de consolidación y estructura",
  "etapa de revisión interna y ajustes",
  "etapa de alianzas y decisiones compartidas",
];

function getSign(month, day) {
  return zodiacRanges.find(({ start, end }) => {
    const [sm, sd] = start;
    const [em, ed] = end;

    if (sm <= em) {
      return (month === sm && day >= sd) || (month === em && day <= ed) || (month > sm && month < em);
    }

    return (month === sm && day >= sd) || (month === em && day <= ed) || month > sm || month < em;
  });
}

function getHourInfluence(hour) {
  if (hour < 6) return "Naciste en un tramo introspectivo: tu energía se renueva en calma y reflexión.";
  if (hour < 12) return "Naciste en un tramo activo: sueles actuar con iniciativa y foco en objetivos.";
  if (hour < 18) return "Naciste en un tramo social: creces en colaboración e intercambio con otros.";
  return "Naciste en un tramo emocional: conectas con profundidad y procesos internos.";
}

function calculateNatalIntensity(day, hour) {
  return (day % 9) + (hour % 6) + 1;
}

function formatTopic(topic) {
  return topic[0].toUpperCase() + topic.slice(1);
}

function renderTopics(sign) {
  const topics = topicsBySign[sign] ?? topicsBySign.Acuario;

  return topicOrder
    .map(
      (topic) => `
      <article class="topic">
        <h3>${formatTopic(topic)}</h3>
        <p>${topics[topic]}</p>
      </article>
    `
    )
    .join("");
}

function createTransitMessage(topic, sign, monthOffset, intensity) {
  const baseTopics = topicsBySign[sign] ?? topicsBySign.Acuario;
  const cycle = (monthOffset + intensity) % 4;
  const tone = seasonalEnergies[cycle];

  return `${tone}; enfoque en ${topic}: ${baseTopics[topic]}`;
}

function generateForecast(sign, currentDate, monthsAhead, natalIntensity) {
  const timeline = [];
  const step = monthsAhead > 24 ? 6 : 3;

  for (let monthOffset = step; monthOffset <= monthsAhead; monthOffset += step) {
    const projectedDate = new Date(Date.UTC(currentDate.getUTCFullYear(), currentDate.getUTCMonth() + monthOffset, 1));
    const periodLabel = projectedDate.toLocaleDateString("es-ES", { month: "long", year: "numeric", timeZone: "UTC" });
    const focusTopic = topicOrder[(monthOffset / step - 1) % topicOrder.length];

    timeline.push({
      period: periodLabel,
      focusTopic,
      message: createTransitMessage(focusTopic, sign, monthOffset, natalIntensity),
    });
  }

  return timeline;
}

function renderForecastTimeline(timeline) {
  return timeline
    .map(
      (item) => `
      <article class="topic">
        <h3>${item.period} · ${formatTopic(item.focusTopic)}</h3>
        <p>${item.message}</p>
      </article>
      `
    )
    .join("");
}

const form = document.getElementById("astro-form");
const result = document.getElementById("result");
const signTitle = document.getElementById("sign-title");
const coreTrait = document.getElementById("core-trait");
const topicsContainer = document.getElementById("topics");
const forecastSection = document.getElementById("forecast");
const currentDateInput = document.getElementById("current-date");
const horizonInput = document.getElementById("horizon");
const forecastSummary = document.getElementById("forecast-summary");
const forecastTimeline = document.getElementById("forecast-timeline");
const forecastButton = document.getElementById("forecast-btn");

let activeBirthContext = null;
currentDateInput.value = new Date().toISOString().slice(0, 10);

function updateForecast() {
  if (!activeBirthContext) {
    return;
  }

  const currentDate = new Date(currentDateInput.value);
  const monthsAhead = Number(horizonInput.value);

  if (Number.isNaN(currentDate.getTime()) || Number.isNaN(monthsAhead)) {
    return;
  }

  const timeline = generateForecast(
    activeBirthContext.sign,
    currentDate,
    monthsAhead,
    activeBirthContext.natalIntensity
  );

  forecastSummary.textContent = `Proyección para ${activeBirthContext.sign} desde ${currentDate.toLocaleDateString("es-ES", {
    timeZone: "UTC",
  })} hasta ${monthsAhead} meses.`;
  forecastTimeline.innerHTML = renderForecastTimeline(timeline);
  forecastSection.classList.remove("hidden");
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const birthDate = new Date(form.birthDate.value);
  const [hour] = form.birthTime.value.split(":").map(Number);

  if (Number.isNaN(birthDate.getTime()) || Number.isNaN(hour)) {
    return;
  }

  const month = birthDate.getUTCMonth() + 1;
  const day = birthDate.getUTCDate();
  const signInfo = getSign(month, day);

  if (!signInfo) {
    return;
  }

  activeBirthContext = {
    sign: signInfo.sign,
    natalIntensity: calculateNatalIntensity(day, hour),
  };

  signTitle.textContent = `Tu signo base es ${signInfo.sign}`;
  coreTrait.textContent = `${signInfo.trait} ${getHourInfluence(hour)}`;
  topicsContainer.innerHTML = renderTopics(signInfo.sign);

  result.classList.remove("hidden");
  updateForecast();
  result.scrollIntoView({ behavior: "smooth", block: "start" });
});

forecastButton.addEventListener("click", updateForecast);
