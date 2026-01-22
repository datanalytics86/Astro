"""
Interpretations Module - Astrological meaning and analysis.

Provides interpretations for planetary positions, aspects, and transits.
Supports multiple languages (Spanish/English).
"""

from typing import Optional
from datetime import datetime, timedelta

# =============================================================================
# TRANSLATIONS
# =============================================================================

TRANSLATIONS = {
    "es": {
        # UI
        "title": "✨ Carta Natal",
        "birth_date": "📅 Fecha de nacimiento",
        "birth_time": "🕐 Hora de nacimiento",
        "latitude": "📍 Latitud",
        "longitude": "📍 Longitud",
        "timezone": "🌍 Zona horaria",
        "calculate": "🔮 Calcular Carta Natal",
        "calculating": "Calculando posiciones planetarias...",
        "success": "✅ Carta calculada",
        "cardinal_points": "🏠 Puntos Cardinales",
        "ascendant": "Ascendente",
        "midheaven": "Medio Cielo",
        "planetary_positions": "🪐 Posiciones Planetarias",
        "main_aspects": "✨ Aspectos Principales",
        "technical_data": "📊 Datos Técnicos",
        "houses": "Casas",
        "house_system": "Sistema de casas",
        "interpretation": "📖 Interpretación",
        "forecast": "🔮 Pronóstico",
        "select_theme": "Selecciona un tema",
        "money": "💰 Dinero y Finanzas",
        "love": "❤️ Amor y Relaciones",
        "career": "💼 Carrera y Trabajo",
        "health": "🏥 Salud y Bienestar",
        "next_months": "Próximos 12 meses",
        "common_cities": "Ciudades comunes:",
        "north_positive": "Norte = positivo, Sur = negativo",
        "east_positive": "Este = positivo, Oeste = negativo",
        "language": "🌐 Idioma",
        "footer": "Astro Engineering - Cálculos de alta precisión usando Swiss Ephemeris",

        # Planets
        "sun": "Sol",
        "moon": "Luna",
        "mercury": "Mercurio",
        "venus": "Venus",
        "mars": "Marte",
        "jupiter": "Júpiter",
        "saturn": "Saturno",
        "uranus": "Urano",
        "neptune": "Neptuno",
        "pluto": "Plutón",

        # Signs
        "Aries": "Aries",
        "Taurus": "Tauro",
        "Gemini": "Géminis",
        "Cancer": "Cáncer",
        "Leo": "Leo",
        "Virgo": "Virgo",
        "Libra": "Libra",
        "Scorpio": "Escorpio",
        "Sagittarius": "Sagitario",
        "Capricorn": "Capricornio",
        "Aquarius": "Acuario",
        "Pisces": "Piscis",

        # Aspects
        "conjunction": "conjunción",
        "opposition": "oposición",
        "trine": "trígono",
        "square": "cuadratura",
        "sextile": "sextil",
    },
    "en": {
        # UI
        "title": "✨ Birth Chart",
        "birth_date": "📅 Birth date",
        "birth_time": "🕐 Birth time",
        "latitude": "📍 Latitude",
        "longitude": "📍 Longitude",
        "timezone": "🌍 Timezone",
        "calculate": "🔮 Calculate Birth Chart",
        "calculating": "Calculating planetary positions...",
        "success": "✅ Chart calculated",
        "cardinal_points": "🏠 Cardinal Points",
        "ascendant": "Ascendant",
        "midheaven": "Midheaven",
        "planetary_positions": "🪐 Planetary Positions",
        "main_aspects": "✨ Main Aspects",
        "technical_data": "📊 Technical Data",
        "houses": "Houses",
        "house_system": "House system",
        "interpretation": "📖 Interpretation",
        "forecast": "🔮 Forecast",
        "select_theme": "Select a theme",
        "money": "💰 Money & Finances",
        "love": "❤️ Love & Relationships",
        "career": "💼 Career & Work",
        "health": "🏥 Health & Wellness",
        "next_months": "Next 12 months",
        "common_cities": "Common cities:",
        "north_positive": "North = positive, South = negative",
        "east_positive": "East = positive, West = negative",
        "language": "🌐 Language",
        "footer": "Astro Engineering - High precision calculations using Swiss Ephemeris",

        # Planets
        "sun": "Sun",
        "moon": "Moon",
        "mercury": "Mercury",
        "venus": "Venus",
        "mars": "Mars",
        "jupiter": "Jupiter",
        "saturn": "Saturn",
        "uranus": "Uranus",
        "neptune": "Neptune",
        "pluto": "Pluto",

        # Signs
        "Aries": "Aries",
        "Taurus": "Taurus",
        "Gemini": "Gemini",
        "Cancer": "Cancer",
        "Leo": "Leo",
        "Virgo": "Virgo",
        "Libra": "Libra",
        "Scorpio": "Scorpio",
        "Sagittarius": "Sagittarius",
        "Capricorn": "Capricorn",
        "Aquarius": "Aquarius",
        "Pisces": "Pisces",

        # Aspects
        "conjunction": "conjunction",
        "opposition": "opposition",
        "trine": "trine",
        "square": "square",
        "sextile": "sextile",
    }
}


# =============================================================================
# PLANET INTERPRETATIONS
# =============================================================================

PLANET_IN_SIGN = {
    "es": {
        "sun": {
            "Aries": "Tu esencia es pionera y valiente. Tienes una energía vital fuerte, necesitas liderar e iniciar proyectos. Personalidad directa y competitiva.",
            "Taurus": "Tu esencia es estable y sensorial. Valoras la seguridad material, el confort y los placeres de la vida. Personalidad persistente y práctica.",
            "Gemini": "Tu esencia es curiosa y comunicativa. Necesitas variedad mental, aprender y compartir ideas. Personalidad versátil y adaptable.",
            "Cancer": "Tu esencia es emotiva y protectora. La familia y el hogar son fundamentales. Personalidad sensible y nurturadora.",
            "Leo": "Tu esencia es creativa y expresiva. Necesitas brillar y ser reconocido. Personalidad generosa y dramática.",
            "Virgo": "Tu esencia es analítica y servicial. Buscas la perfección y la utilidad práctica. Personalidad meticulosa y trabajadora.",
            "Libra": "Tu esencia busca el equilibrio y la armonía. Las relaciones son fundamentales. Personalidad diplomática y estética.",
            "Scorpio": "Tu esencia es intensa y transformadora. Buscas la verdad profunda. Personalidad magnética y reservada.",
            "Sagittarius": "Tu esencia es aventurera y filosófica. Buscas expandir horizontes y encontrar significado. Personalidad optimista y directa.",
            "Capricorn": "Tu esencia es ambiciosa y responsable. Buscas logros concretos y reconocimiento. Personalidad disciplinada y perseverante.",
            "Aquarius": "Tu esencia es innovadora y humanitaria. Buscas la originalidad y el progreso colectivo. Personalidad independiente y visionaria.",
            "Pisces": "Tu esencia es compasiva y espiritual. Tienes gran sensibilidad e intuición. Personalidad soñadora y empática.",
        },
        "moon": {
            "Aries": "Emocionalmente necesitas acción e independencia. Reaccionas rápido y con intensidad. Tus emociones son directas.",
            "Taurus": "Emocionalmente necesitas seguridad y estabilidad. Eres constante en tus afectos. Buscas confort emocional.",
            "Gemini": "Emocionalmente necesitas comunicación y variedad. Procesas sentimientos a través de las palabras. Mente y emociones conectadas.",
            "Cancer": "Emocionalmente eres muy sensible y protector. La familia es tu refugio. Memoria emocional muy fuerte.",
            "Leo": "Emocionalmente necesitas reconocimiento y afecto. Generoso con tus seres queridos. Orgullo emocional.",
            "Virgo": "Emocionalmente necesitas orden y utilidad. Analizas tus sentimientos. Cuidas a otros de forma práctica.",
            "Libra": "Emocionalmente necesitas armonía y compañía. Evitas conflictos. Buscas equilibrio en relaciones.",
            "Scorpio": "Emocionalmente eres intenso y profundo. Sientes con gran pasión. Necesitas intimidad verdadera.",
            "Sagittarius": "Emocionalmente necesitas libertad y aventura. Optimista por naturaleza. Buscas significado en las emociones.",
            "Capricorn": "Emocionalmente eres reservado y responsable. Maduras emocionalmente con el tiempo. Control emocional.",
            "Aquarius": "Emocionalmente necesitas espacio e independencia. Racionalizas los sentimientos. Amistad es importante.",
            "Pisces": "Emocionalmente eres muy sensible e intuitivo. Absorbes emociones ajenas. Gran compasión y empatía.",
        },
        "mercury": {
            "Aries": "Mente rápida y directa. Piensas con urgencia. Comunicación impulsiva pero honesta.",
            "Taurus": "Mente práctica y metódica. Piensas despacio pero con profundidad. Buena memoria.",
            "Gemini": "Mente ágil y versátil. Gran capacidad de aprendizaje. Comunicador nato.",
            "Cancer": "Mente intuitiva y emocional. Buena memoria del pasado. Comunicación empática.",
            "Leo": "Mente creativa y expresiva. Piensas en grande. Comunicación dramática.",
            "Virgo": "Mente analítica y detallista. Pensamiento crítico desarrollado. Comunicación precisa.",
            "Libra": "Mente equilibrada y diplomática. Ves todos los puntos de vista. Comunicación elegante.",
            "Scorpio": "Mente investigadora y penetrante. Piensas profundamente. Comunicación estratégica.",
            "Sagittarius": "Mente filosófica y expansiva. Piensas en grande. Comunicación entusiasta.",
            "Capricorn": "Mente estructurada y práctica. Pensamiento orientado a metas. Comunicación seria.",
            "Aquarius": "Mente innovadora y original. Pensamiento futurista. Comunicación única.",
            "Pisces": "Mente intuitiva e imaginativa. Pensamiento no lineal. Comunicación poética.",
        },
        "venus": {
            "Aries": "En el amor eres apasionado y directo. Te atraen personas independientes. Conquistas activamente.",
            "Taurus": "En el amor eres sensual y leal. Valoras estabilidad. Disfrutas placeres materiales.",
            "Gemini": "En el amor necesitas comunicación. Te atraen personas inteligentes. Coqueteo mental.",
            "Cancer": "En el amor eres protector y nurturador. Buscas seguridad emocional. Muy familiar.",
            "Leo": "En el amor eres romántico y generoso. Necesitas admiración. Amor dramático.",
            "Virgo": "En el amor eres servicial y dedicado. Demuestras amor con actos. Selectivo en pareja.",
            "Libra": "En el amor buscas equilibrio y armonía. Muy romántico. Necesitas compañía.",
            "Scorpio": "En el amor eres intenso y profundo. Pasión transformadora. Lealtad absoluta.",
            "Sagittarius": "En el amor necesitas libertad y aventura. Optimista en relaciones. Amor expansivo.",
            "Capricorn": "En el amor eres serio y comprometido. Buscas estabilidad. Amor que crece con el tiempo.",
            "Aquarius": "En el amor necesitas libertad e independencia. Amistad primero. Amor no convencional.",
            "Pisces": "En el amor eres romántico e idealista. Gran entrega. Amor incondicional.",
        },
        "mars": {
            "Aries": "Tu energía es potente y directa. Actúas con decisión. Gran iniciativa y competitividad.",
            "Taurus": "Tu energía es constante y determinada. Actúas con paciencia. Resistencia y perseverancia.",
            "Gemini": "Tu energía es mental y versátil. Actúas con rapidez. Múltiples proyectos simultáneos.",
            "Cancer": "Tu energía se activa para proteger. Actúas emocionalmente. Defiendes a los tuyos.",
            "Leo": "Tu energía es creativa y expresiva. Actúas con confianza. Liderazgo natural.",
            "Virgo": "Tu energía es metódica y precisa. Actúas con eficiencia. Trabajo detallado.",
            "Libra": "Tu energía busca equilibrio. Actúas diplomáticamente. Evitas confrontación directa.",
            "Scorpio": "Tu energía es intensa y estratégica. Actúas con determinación. Poder transformador.",
            "Sagittarius": "Tu energía es expansiva y aventurera. Actúas con optimismo. Acción en grande.",
            "Capricorn": "Tu energía es ambiciosa y disciplinada. Actúas con estrategia. Logros a largo plazo.",
            "Aquarius": "Tu energía es innovadora y rebelde. Actúas de forma única. Causas colectivas.",
            "Pisces": "Tu energía es sutil e inspirada. Actúas intuitivamente. Acción compasiva.",
        },
        "jupiter": {
            "Aries": "Tu expansión viene a través del liderazgo y la iniciativa. Suerte en nuevos comienzos.",
            "Taurus": "Tu expansión viene a través de recursos materiales. Suerte en finanzas y bienes.",
            "Gemini": "Tu expansión viene a través del conocimiento. Suerte en comunicación y aprendizaje.",
            "Cancer": "Tu expansión viene a través de la familia. Suerte en hogar y bienes raíces.",
            "Leo": "Tu expansión viene a través de la creatividad. Suerte en expresión personal.",
            "Virgo": "Tu expansión viene a través del servicio. Suerte en trabajo y salud.",
            "Libra": "Tu expansión viene a través de las asociaciones. Suerte en relaciones y arte.",
            "Scorpio": "Tu expansión viene a través de la transformación. Suerte en inversiones.",
            "Sagittarius": "Tu expansión es natural y amplia. Suerte en viajes y filosofía.",
            "Capricorn": "Tu expansión viene a través del esfuerzo. Suerte en carrera y status.",
            "Aquarius": "Tu expansión viene a través de la innovación. Suerte en grupos y tecnología.",
            "Pisces": "Tu expansión viene a través de la espiritualidad. Suerte en arte y sanación.",
        },
        "saturn": {
            "Aries": "Tu lección kármica es sobre la paciencia y el ego. Aprendes a liderar con madurez.",
            "Taurus": "Tu lección kármica es sobre la seguridad material. Aprendes el verdadero valor.",
            "Gemini": "Tu lección kármica es sobre la comunicación. Aprendes a pensar con profundidad.",
            "Cancer": "Tu lección kármica es sobre la familia. Aprendes sobre responsabilidad emocional.",
            "Leo": "Tu lección kármica es sobre el ego y la creatividad. Aprendes humildad.",
            "Virgo": "Tu lección kármica es sobre el servicio y la perfección. Aprendes a soltar el control.",
            "Libra": "Tu lección kármica es sobre las relaciones. Aprendes sobre compromiso real.",
            "Scorpio": "Tu lección kármica es sobre el poder y control. Aprendes transformación consciente.",
            "Sagittarius": "Tu lección kármica es sobre la verdad y libertad. Aprendes responsabilidad.",
            "Capricorn": "Tu lección kármica es sobre la ambición. Aprendes liderazgo con integridad.",
            "Aquarius": "Tu lección kármica es sobre la individualidad. Aprendes a pertenecer siendo único.",
            "Pisces": "Tu lección kármica es sobre la espiritualidad. Aprendes límites saludables.",
        },
    },
    "en": {
        "sun": {
            "Aries": "Your essence is pioneering and brave. You have strong vital energy, need to lead and initiate projects. Direct and competitive personality.",
            "Taurus": "Your essence is stable and sensory. You value material security, comfort and life's pleasures. Persistent and practical personality.",
            "Gemini": "Your essence is curious and communicative. You need mental variety, learning and sharing ideas. Versatile and adaptable personality.",
            "Cancer": "Your essence is emotional and protective. Family and home are fundamental. Sensitive and nurturing personality.",
            "Leo": "Your essence is creative and expressive. You need to shine and be recognized. Generous and dramatic personality.",
            "Virgo": "Your essence is analytical and helpful. You seek perfection and practical utility. Meticulous and hardworking personality.",
            "Libra": "Your essence seeks balance and harmony. Relationships are fundamental. Diplomatic and aesthetic personality.",
            "Scorpio": "Your essence is intense and transformative. You seek deep truth. Magnetic and reserved personality.",
            "Sagittarius": "Your essence is adventurous and philosophical. You seek to expand horizons and find meaning. Optimistic and direct personality.",
            "Capricorn": "Your essence is ambitious and responsible. You seek concrete achievements and recognition. Disciplined and perseverant personality.",
            "Aquarius": "Your essence is innovative and humanitarian. You seek originality and collective progress. Independent and visionary personality.",
            "Pisces": "Your essence is compassionate and spiritual. You have great sensitivity and intuition. Dreamy and empathic personality.",
        },
        "moon": {
            "Aries": "Emotionally you need action and independence. You react quickly and intensely. Your emotions are direct.",
            "Taurus": "Emotionally you need security and stability. You are constant in your affections. You seek emotional comfort.",
            "Gemini": "Emotionally you need communication and variety. You process feelings through words. Mind and emotions connected.",
            "Cancer": "Emotionally you are very sensitive and protective. Family is your refuge. Very strong emotional memory.",
            "Leo": "Emotionally you need recognition and affection. Generous with loved ones. Emotional pride.",
            "Virgo": "Emotionally you need order and utility. You analyze your feelings. You care for others practically.",
            "Libra": "Emotionally you need harmony and company. You avoid conflicts. You seek balance in relationships.",
            "Scorpio": "Emotionally you are intense and deep. You feel with great passion. You need true intimacy.",
            "Sagittarius": "Emotionally you need freedom and adventure. Optimistic by nature. You seek meaning in emotions.",
            "Capricorn": "Emotionally you are reserved and responsible. You mature emotionally over time. Emotional control.",
            "Aquarius": "Emotionally you need space and independence. You rationalize feelings. Friendship is important.",
            "Pisces": "Emotionally you are very sensitive and intuitive. You absorb others' emotions. Great compassion and empathy.",
        },
        "mercury": {
            "Aries": "Quick and direct mind. You think with urgency. Impulsive but honest communication.",
            "Taurus": "Practical and methodical mind. You think slowly but deeply. Good memory.",
            "Gemini": "Agile and versatile mind. Great learning capacity. Born communicator.",
            "Cancer": "Intuitive and emotional mind. Good memory of the past. Empathic communication.",
            "Leo": "Creative and expressive mind. You think big. Dramatic communication.",
            "Virgo": "Analytical and detail-oriented mind. Developed critical thinking. Precise communication.",
            "Libra": "Balanced and diplomatic mind. You see all points of view. Elegant communication.",
            "Scorpio": "Investigative and penetrating mind. You think deeply. Strategic communication.",
            "Sagittarius": "Philosophical and expansive mind. You think big. Enthusiastic communication.",
            "Capricorn": "Structured and practical mind. Goal-oriented thinking. Serious communication.",
            "Aquarius": "Innovative and original mind. Futuristic thinking. Unique communication.",
            "Pisces": "Intuitive and imaginative mind. Non-linear thinking. Poetic communication.",
        },
        "venus": {
            "Aries": "In love you are passionate and direct. You're attracted to independent people. You actively conquer.",
            "Taurus": "In love you are sensual and loyal. You value stability. You enjoy material pleasures.",
            "Gemini": "In love you need communication. You're attracted to intelligent people. Mental flirting.",
            "Cancer": "In love you are protective and nurturing. You seek emotional security. Very family-oriented.",
            "Leo": "In love you are romantic and generous. You need admiration. Dramatic love.",
            "Virgo": "In love you are helpful and dedicated. You show love through acts. Selective in partner.",
            "Libra": "In love you seek balance and harmony. Very romantic. You need company.",
            "Scorpio": "In love you are intense and deep. Transformative passion. Absolute loyalty.",
            "Sagittarius": "In love you need freedom and adventure. Optimistic in relationships. Expansive love.",
            "Capricorn": "In love you are serious and committed. You seek stability. Love that grows over time.",
            "Aquarius": "In love you need freedom and independence. Friendship first. Unconventional love.",
            "Pisces": "In love you are romantic and idealistic. Great devotion. Unconditional love.",
        },
        "mars": {
            "Aries": "Your energy is powerful and direct. You act with decision. Great initiative and competitiveness.",
            "Taurus": "Your energy is constant and determined. You act with patience. Resistance and perseverance.",
            "Gemini": "Your energy is mental and versatile. You act quickly. Multiple simultaneous projects.",
            "Cancer": "Your energy activates to protect. You act emotionally. You defend your own.",
            "Leo": "Your energy is creative and expressive. You act with confidence. Natural leadership.",
            "Virgo": "Your energy is methodical and precise. You act efficiently. Detailed work.",
            "Libra": "Your energy seeks balance. You act diplomatically. You avoid direct confrontation.",
            "Scorpio": "Your energy is intense and strategic. You act with determination. Transformative power.",
            "Sagittarius": "Your energy is expansive and adventurous. You act with optimism. Action on a grand scale.",
            "Capricorn": "Your energy is ambitious and disciplined. You act strategically. Long-term achievements.",
            "Aquarius": "Your energy is innovative and rebellious. You act uniquely. Collective causes.",
            "Pisces": "Your energy is subtle and inspired. You act intuitively. Compassionate action.",
        },
        "jupiter": {
            "Aries": "Your expansion comes through leadership and initiative. Luck in new beginnings.",
            "Taurus": "Your expansion comes through material resources. Luck in finances and assets.",
            "Gemini": "Your expansion comes through knowledge. Luck in communication and learning.",
            "Cancer": "Your expansion comes through family. Luck in home and real estate.",
            "Leo": "Your expansion comes through creativity. Luck in personal expression.",
            "Virgo": "Your expansion comes through service. Luck in work and health.",
            "Libra": "Your expansion comes through partnerships. Luck in relationships and art.",
            "Scorpio": "Your expansion comes through transformation. Luck in investments.",
            "Sagittarius": "Your expansion is natural and broad. Luck in travel and philosophy.",
            "Capricorn": "Your expansion comes through effort. Luck in career and status.",
            "Aquarius": "Your expansion comes through innovation. Luck in groups and technology.",
            "Pisces": "Your expansion comes through spirituality. Luck in art and healing.",
        },
        "saturn": {
            "Aries": "Your karmic lesson is about patience and ego. You learn to lead with maturity.",
            "Taurus": "Your karmic lesson is about material security. You learn true value.",
            "Gemini": "Your karmic lesson is about communication. You learn to think deeply.",
            "Cancer": "Your karmic lesson is about family. You learn about emotional responsibility.",
            "Leo": "Your karmic lesson is about ego and creativity. You learn humility.",
            "Virgo": "Your karmic lesson is about service and perfection. You learn to let go of control.",
            "Libra": "Your karmic lesson is about relationships. You learn about real commitment.",
            "Scorpio": "Your karmic lesson is about power and control. You learn conscious transformation.",
            "Sagittarius": "Your karmic lesson is about truth and freedom. You learn responsibility.",
            "Capricorn": "Your karmic lesson is about ambition. You learn leadership with integrity.",
            "Aquarius": "Your karmic lesson is about individuality. You learn to belong while being unique.",
            "Pisces": "Your karmic lesson is about spirituality. You learn healthy boundaries.",
        },
    }
}


# =============================================================================
# HOUSE MEANINGS (for forecasts)
# =============================================================================

HOUSE_THEMES = {
    "es": {
        1: "identidad, apariencia, nuevos comienzos",
        2: "dinero, recursos, valores personales",
        3: "comunicación, hermanos, viajes cortos",
        4: "hogar, familia, raíces, padre/madre",
        5: "creatividad, romance, hijos, diversión",
        6: "trabajo diario, salud, servicio",
        7: "pareja, socios, contratos, otros",
        8: "transformación, sexualidad, dinero de otros",
        9: "filosofía, viajes largos, estudios superiores",
        10: "carrera, reputación, logros públicos",
        11: "amigos, grupos, esperanzas, futuro",
        12: "espiritualidad, inconsciente, retiro",
    },
    "en": {
        1: "identity, appearance, new beginnings",
        2: "money, resources, personal values",
        3: "communication, siblings, short trips",
        4: "home, family, roots, father/mother",
        5: "creativity, romance, children, fun",
        6: "daily work, health, service",
        7: "partner, associates, contracts, others",
        8: "transformation, sexuality, others' money",
        9: "philosophy, long trips, higher education",
        10: "career, reputation, public achievements",
        11: "friends, groups, hopes, future",
        12: "spirituality, unconscious, retreat",
    }
}


# =============================================================================
# FORECAST INTERPRETATIONS BY THEME
# =============================================================================

TRANSIT_INTERPRETATIONS = {
    "es": {
        "money": {
            "jupiter_2": "**Excelente período para las finanzas.** Júpiter en tu casa 2 trae expansión de recursos, nuevas fuentes de ingreso y oportunidades de crecimiento financiero. Es buen momento para inversiones.",
            "jupiter_8": "**Posibilidad de herencias o dinero de otros.** Júpiter en casa 8 puede traer beneficios a través de asociaciones, inversiones conjuntas o recursos compartidos.",
            "saturn_2": "**Período de consolidación financiera.** Saturno en casa 2 pide disciplina con el dinero. Puede haber restricciones iniciales pero construyes bases sólidas.",
            "saturn_10": "**Trabajo duro que trae recompensas.** Saturno en casa 10 puede significar más responsabilidades laborales, pero también reconocimiento y avance en la carrera.",
            "uranus_2": "**Cambios inesperados en finanzas.** Urano en casa 2 trae sorpresas monetarias - tanto ganancias inesperadas como gastos imprevistos. Flexibilidad es clave.",
            "pluto_2": "**Transformación profunda de valores.** Plutón en casa 2 regenera tu relación con el dinero y los recursos. Cambios intensos pero liberadores.",
            "neptune_2": "**Cuidado con las finanzas.** Neptuno en casa 2 puede traer confusión financiera. Evita inversiones riesgosas y revisa bien los contratos.",
        },
        "love": {
            "jupiter_5": "**Excelente para el romance.** Júpiter en casa 5 expande las oportunidades amorosas, trae alegría y posibles encuentros significativos.",
            "jupiter_7": "**Expansión en relaciones.** Júpiter en casa 7 favorece compromisos, matrimonio o asociaciones beneficiosas. Las relaciones crecen.",
            "saturn_5": "**Romance serio o restricciones.** Saturno en casa 5 puede traer relaciones maduras o un período de menos diversión romántica.",
            "saturn_7": "**Pruebas en relaciones.** Saturno en casa 7 examina tus relaciones. Las sólidas se fortalecen, las débiles pueden terminar.",
            "uranus_5": "**Romances inesperados.** Urano en casa 5 trae encuentros sorpresivos y relaciones no convencionales. Emoción y libertad.",
            "uranus_7": "**Cambios en pareja.** Urano en casa 7 puede traer separaciones o renovación total de la relación. Necesidad de libertad.",
            "pluto_7": "**Transformación de relaciones.** Plutón en casa 7 intensifica las relaciones. Puede haber crisis que llevan a renovación profunda.",
            "venus_return": "**Tu Venus Return trae un año favorable para el amor.** Es buen momento para iniciar relaciones o mejorar las existentes.",
        },
        "career": {
            "jupiter_10": "**Excelente para la carrera.** Júpiter en casa 10 trae expansión profesional, reconocimiento y posibles promociones.",
            "jupiter_6": "**Mejora en el trabajo diario.** Júpiter en casa 6 beneficia tu ambiente laboral y puede traer mejores condiciones de trabajo.",
            "saturn_10": "**Período de mucha responsabilidad.** Saturno en casa 10 exige trabajo duro pero construye tu reputación profesional a largo plazo.",
            "saturn_6": "**Disciplina en el trabajo.** Saturno en casa 6 puede traer más carga laboral pero también estructura y eficiencia.",
            "uranus_10": "**Cambios de carrera.** Urano en casa 10 puede traer cambios inesperados en tu profesión. Posible reinvención profesional.",
            "pluto_10": "**Transformación profesional profunda.** Plutón en casa 10 regenera tu carrera. Puede haber crisis de poder pero también empoderamiento.",
            "mars_10": "**Energía para avanzar.** Marte transitando casa 10 da impulso para lograr metas profesionales. Buen momento para actuar.",
        },
        "health": {
            "jupiter_6": "**Período favorable para la salud.** Júpiter en casa 6 mejora el bienestar general y puede traer sanación.",
            "saturn_6": "**Atención a la salud.** Saturno en casa 6 pide disciplina en hábitos de salud. Posibles revisiones médicas necesarias.",
            "neptune_6": "**Sensibilidad en salud.** Neptuno en casa 6 aumenta la sensibilidad física. Cuidado con autodiagnósticos y sustancias.",
            "pluto_6": "**Regeneración física.** Plutón en casa 6 puede traer transformación en hábitos de salud. Posible sanación profunda.",
            "mars_6": "**Energía fluctuante.** Marte en casa 6 da energía pero puede traer tensión. Cuidado con accidentes menores.",
            "jupiter_1": "**Vitalidad aumentada.** Júpiter en casa 1 mejora tu energía general y optimismo. Buen momento para comenzar rutinas saludables.",
        },
    },
    "en": {
        "money": {
            "jupiter_2": "**Excellent period for finances.** Jupiter in your 2nd house brings resource expansion, new income sources, and financial growth opportunities. Good time for investments.",
            "jupiter_8": "**Possibility of inheritances or others' money.** Jupiter in 8th house can bring benefits through partnerships, joint investments, or shared resources.",
            "saturn_2": "**Period of financial consolidation.** Saturn in 2nd house demands money discipline. There may be initial restrictions but you build solid foundations.",
            "saturn_10": "**Hard work bringing rewards.** Saturn in 10th house may mean more work responsibilities, but also recognition and career advancement.",
            "uranus_2": "**Unexpected financial changes.** Uranus in 2nd house brings monetary surprises - both unexpected gains and unforeseen expenses. Flexibility is key.",
            "pluto_2": "**Deep transformation of values.** Pluto in 2nd house regenerates your relationship with money and resources. Intense but liberating changes.",
            "neptune_2": "**Caution with finances.** Neptune in 2nd house can bring financial confusion. Avoid risky investments and review contracts carefully.",
        },
        "love": {
            "jupiter_5": "**Excellent for romance.** Jupiter in 5th house expands love opportunities, brings joy, and possible significant encounters.",
            "jupiter_7": "**Expansion in relationships.** Jupiter in 7th house favors commitments, marriage, or beneficial partnerships. Relationships grow.",
            "saturn_5": "**Serious romance or restrictions.** Saturn in 5th house may bring mature relationships or a period of less romantic fun.",
            "saturn_7": "**Tests in relationships.** Saturn in 7th house examines your relationships. Solid ones strengthen, weak ones may end.",
            "uranus_5": "**Unexpected romances.** Uranus in 5th house brings surprising encounters and unconventional relationships. Excitement and freedom.",
            "uranus_7": "**Changes in partnership.** Uranus in 7th house may bring separations or total relationship renewal. Need for freedom.",
            "pluto_7": "**Transformation of relationships.** Pluto in 7th house intensifies relationships. There may be crises leading to deep renewal.",
            "venus_return": "**Your Venus Return brings a favorable year for love.** Good time to start relationships or improve existing ones.",
        },
        "career": {
            "jupiter_10": "**Excellent for career.** Jupiter in 10th house brings professional expansion, recognition, and possible promotions.",
            "jupiter_6": "**Improvement in daily work.** Jupiter in 6th house benefits your work environment and may bring better working conditions.",
            "saturn_10": "**Period of great responsibility.** Saturn in 10th house demands hard work but builds your long-term professional reputation.",
            "saturn_6": "**Discipline at work.** Saturn in 6th house may bring more workload but also structure and efficiency.",
            "uranus_10": "**Career changes.** Uranus in 10th house may bring unexpected changes in your profession. Possible professional reinvention.",
            "pluto_10": "**Deep professional transformation.** Pluto in 10th house regenerates your career. There may be power crises but also empowerment.",
            "mars_10": "**Energy to advance.** Mars transiting 10th house gives momentum to achieve professional goals. Good time to act.",
        },
        "health": {
            "jupiter_6": "**Favorable period for health.** Jupiter in 6th house improves general wellbeing and may bring healing.",
            "saturn_6": "**Health attention.** Saturn in 6th house demands discipline in health habits. Possible necessary medical checkups.",
            "neptune_6": "**Health sensitivity.** Neptune in 6th house increases physical sensitivity. Beware of self-diagnosis and substances.",
            "pluto_6": "**Physical regeneration.** Pluto in 6th house may bring transformation in health habits. Possible deep healing.",
            "mars_6": "**Fluctuating energy.** Mars in 6th house gives energy but may bring tension. Beware of minor accidents.",
            "jupiter_1": "**Increased vitality.** Jupiter in 1st house improves your general energy and optimism. Good time to start healthy routines.",
        },
    }
}


def get_translation(key: str, lang: str = "es") -> str:
    """Get translated string."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["es"]).get(key, key)


def get_planet_interpretation(planet: str, sign: str, lang: str = "es") -> str:
    """Get interpretation for planet in sign."""
    interpretations = PLANET_IN_SIGN.get(lang, PLANET_IN_SIGN["es"])
    planet_data = interpretations.get(planet.lower(), {})
    return planet_data.get(sign, "")


def get_forecast_interpretation(transit_key: str, theme: str, lang: str = "es") -> str:
    """Get forecast interpretation for a transit and theme."""
    theme_data = TRANSIT_INTERPRETATIONS.get(lang, TRANSIT_INTERPRETATIONS["es"]).get(theme, {})
    return theme_data.get(transit_key, "")


def get_house_theme(house: int, lang: str = "es") -> str:
    """Get theme description for a house."""
    return HOUSE_THEMES.get(lang, HOUSE_THEMES["es"]).get(house, "")
