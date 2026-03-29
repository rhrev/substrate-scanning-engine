import React, { useState } from "react";

const C = {
  bg: "#0a0e14",
  card: "#121a26",
  cardAlt: "#182030",
  accent: "#d4a017",
  cyan: "#4db8c2",
  red: "#c94040",
  green: "#4a9e5c",
  magenta: "#a86cc1",
  text: "#cdd3da",
  muted: "#5e7080",
  border: "#1e3040",
  dim: "#3a4e60",
};

const questions = [
  {
    id: "Q1",
    title: "Universalidad del deficit negativo",
    status: "ABIERTA",
    priority: "ALTA",
    color: C.red,
    context: "Para half-reptend primes con p = 7 (mod 8), la suma de digitos del periodo S es siempre menor que k/2. En 961 primos verificados (p < 50,000), no hay una sola excepcion. La desviacion S - k/2 toma valores en -(2n+1)/2 con media -39.3 y rango [-178.5, 0].",
    question: "Por que S - k/2 < 0 universalmente? El primer digito d1 = 0 explica un deficit de -0.5, pero la desviacion acumulada crece con p. Que mecanismo impide que el deficit sea positivo?",
    connections: [
      "Valuacion 2-adica: v2(p-1) = 1 exactamente para p = 7 (mod 8). Esto restringe la estructura del grupo multiplicativo.",
      "Subgrupo de cuadrados: 2 es QR mod p, la orbita de 2 en los cuadrados de (Z/pZ)* tiene estructura asimetrica cuando k es impar.",
      "Paper 4 (Serie I): la identidad S_b(p) = (b-1)lambda/2 fue verificada para co-length impar. Co-length par (lambda = 2) es exactamente este caso no cubierto.",
    ],
    attack: "Computar v2(p-1) para cada half-reptend con p = 7 (mod 8) y correlacionar con |S - k/2|. Si la desviacion escala con v2(p-1), el mecanismo es la profundidad 2-adica de la factorizacion de p-1.",
  },
  {
    id: "Q2",
    title: "Half-reptend con densidad 0.496 vs 0.500: formula cerrada?",
    status: "ABIERTA",
    priority: "ALTA",
    color: C.accent,
    context: "La densidad del periodo para half-reptend con p = 7 (mod 8) es 0.4918 en promedio, pero NO es constante: sigma = 0.013. La densidad varia entre primos individuales. Para p = 1 (mod 8), la densidad es 0.5 exacto con sigma = 0 (Midy).",
    question: "Existe una formula cerrada para S(p) cuando ord2(p) = (p-1)/2 y k es impar? El valor S = (k-1)/2 corresponderia a densidad = (k-1)/(2k), pero S puede ser mucho menor que eso.",
    connections: [
      "La distribucion de S - k/2 tiene cola pesada hacia valores negativos grandes, sugiriendo que no es una simple caminata aleatoria con sesgo fijo.",
      "La desviacion maxima observada (-178.5) ocurre para primos grandes, pero la relacion con p no es monotona.",
    ],
    attack: "Expresar S(p) en terminos de sumas de caracteres o sumas exponenciales sobre (Z/pZ)*. La suma de digitos binarios de 1/p esta relacionada con la traza de Frobenius en ciertos contextos.",
  },
  {
    id: "Q3",
    title: "Gradiente posicional Q1 > Q4",
    status: "ABIERTA",
    priority: "MEDIA",
    color: C.cyan,
    context: "El deficit de densidad en half-reptend (p = 7 mod 8) no es uniforme a lo largo del periodo. Q1 tiene densidad 0.488, Q4 tiene 0.497. El deficit se concentra en los primeros digitos (potencias negativas bajas de 2).",
    question: "El gradiente es consecuencia puramente de d1 = 0 propagandose, o hay estructura adicional en la distribucion de digitos tempranos vs tardios?",
    connections: [
      "d1 = floor(2/p) = 0 para p > 2. Los primeros ~log2(p) digitos estan determinados por la expansion binaria de 1/p antes de que el periodo se estabilice.",
      "Para full-reptend, el gradiente es mucho mas debil (Q1 = 0.495 vs Q4 = 0.501), sugiriendo que la complementariedad de Midy 'corrige' el sesgo inicial.",
    ],
    attack: "Separar los primos p = 7 (mod 8) por tamano y ver si el gradiente se aplana o se acentua. Si se aplana con p grande, el efecto es de borde; si se mantiene, hay estructura profunda.",
  },
  {
    id: "Q4",
    title: "Autocorrelacion lag-1 en half-reptend",
    status: "OBSERVACION",
    priority: "MEDIA",
    color: C.magenta,
    context: "Los digitos del periodo de half-reptend tienen autocorrelacion lag-1 de +0.006, un orden de magnitud mayor que full-reptend (+0.00003). Esto significa que hay ligeramente mas pares (1,1) y (0,0) consecutivos que lo esperado por independencia.",
    question: "La autocorrelacion es consecuencia mecanica del deficit (mas 0s que 1s implica mas pares 0,0), o refleja estructura multiplicativa adicional en la orbita de 2 mod p?",
    connections: [
      "Si la autocorrelacion fuera solo consecuencia del deficit de densidad d = 0.492, el valor esperado seria aprox 4*d*(1-d) - 1 = -0.001, no +0.006. El exceso sugiere correlacion genuina.",
      "La autocorrelacion en lag 3 es negativa (-0.003), creando un patron oscilatorio debil.",
    ],
    attack: "Condicionar la autocorrelacion por p mod 8. Si desaparece para p = 1 (mod 8), confirma que es consecuencia del deficit. Si persiste, es estructura independiente.",
  },
  {
    id: "Q5",
    title: "Deficit de palindromos binarios en primos",
    status: "OBSERVACION",
    priority: "BAJA",
    color: C.green,
    context: "Los primos tienen 187 palindromos binarios (p < 10^6) vs 351 esperados por el null model de impares aleatorios. La primalidad REDUCE la simetria binaria en un factor ~0.53.",
    question: "El deficit de palindromos escala como pi(x) / null(x) para x grande, o converge a alguna constante? Hay una formula para la densidad de primos palindromicos binarios?",
    connections: [
      "Un palindromo binario de n bits tiene ~n/2 grados de libertad. La densidad de primos entre palindromos deberia ser ~2/(n ln 2^n) = 2/(n^2 ln 2) si fueran 'aleatorios', lo cual ya predice un deficit respecto a impares generales.",
      "Los primos de Mersenne (2^k - 1) son palindromos binarios triviales (todo-unos). Pero solo hay 4 Mersenne en este rango.",
    ],
    attack: "Extender a 10^7 y ajustar la fraccion palindromos_primos / palindromos_impares como funcion de x. Comparar con la prediccion heuristica 2/(n^2 ln 2).",
  },
  {
    id: "Q6",
    title: "Senal debil en |delta-ratio| vs XOR consecutivo",
    status: "OBSERVACION",
    priority: "BAJA",
    color: C.dim,
    context: "La diferencia absoluta de ratios ord2(p)/(p-1) entre primos consecutivos tiene correlacion Spearman rho = -0.077 con el Hamming weight del XOR consecutivo. p = 10^-104, estadisticamente real pero efecto microscopico.",
    question: "Es puramente un efecto de que primos cercanos en magnitud tienden a tener p-1 con factorizaciones similares, o hay un acoplamiento mas profundo entre estructura multiplicativa y gaps?",
    connections: [
      "Los gaps entre primos estan conjeturalmente distribuidos como Poisson con parametro ln(p), pero la estructura multiplicativa de p-1 introduce correlaciones locales.",
      "Conexion potencial con la conjetura de Artin generalizada: si p y p+2g son ambos primos, sus ordenes multiplicativos estan parcialmente correlacionados a traves de los factores comunes de p-1 y p+2g-1.",
    ],
    attack: "Estratificar por tamano de gap: para gaps = 2 (primos gemelos), medir la correlacion de ratios. Si la correlacion es mas fuerte para gaps pequenos, confirma el mecanismo de factorizacion compartida.",
  },
];

function Tag({ text, color }) {
  return (
    <span style={{
      display: "inline-block",
      background: color + "20",
      color: color,
      border: "1px solid " + color + "40",
      borderRadius: 4,
      padding: "2px 8px",
      fontSize: 9,
      fontWeight: 700,
      letterSpacing: 1,
      textTransform: "uppercase",
      marginRight: 6,
    }}>{text}</span>
  );
}

function QuestionCard({ q, isOpen, onToggle }) {
  return (
    <div style={{
      background: C.card,
      border: "1px solid " + (isOpen ? q.color + "50" : C.border),
      borderRadius: 8,
      marginBottom: 10,
      overflow: "hidden",
      transition: "border-color 0.2s",
    }}>
      <div
        onClick={onToggle}
        style={{
          padding: "14px 16px",
          cursor: "pointer",
          display: "flex",
          alignItems: "flex-start",
          gap: 12,
        }}
      >
        <div style={{
          fontFamily: "monospace",
          color: q.color,
          fontSize: 13,
          fontWeight: 700,
          flexShrink: 0,
          marginTop: 1,
        }}>{q.id}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, flexWrap: "wrap" }}>
            <Tag text={q.status} color={q.status === "ABIERTA" ? q.color : C.muted} />
            <Tag text={q.priority} color={q.priority === "ALTA" ? C.red : q.priority === "MEDIA" ? C.accent : C.muted} />
          </div>
          <div style={{ color: C.text, fontSize: 13, fontWeight: 600, lineHeight: 1.4 }}>{q.title}</div>
        </div>
        <div style={{
          color: C.muted,
          fontSize: 18,
          flexShrink: 0,
          transform: isOpen ? "rotate(90deg)" : "none",
          transition: "transform 0.2s",
        }}>&#9654;</div>
      </div>

      {isOpen && (
        <div style={{ padding: "0 16px 16px 16px" }}>
          <div style={{ borderTop: "1px solid " + C.border, paddingTop: 14 }}>

            <div style={{ marginBottom: 14 }}>
              <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 6 }}>Contexto</div>
              <div style={{ color: C.text, fontSize: 12, lineHeight: 1.7, padding: "10px 12px", background: C.cardAlt, borderRadius: 5, borderLeft: "3px solid " + C.muted }}>
                {q.context}
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 6 }}>Pregunta</div>
              <div style={{ color: q.color, fontSize: 13, lineHeight: 1.7, padding: "10px 12px", background: q.color + "08", borderRadius: 5, borderLeft: "3px solid " + q.color, fontWeight: 500 }}>
                {q.question}
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 6 }}>Conexiones</div>
              <div style={{ padding: "8px 12px", background: C.cardAlt, borderRadius: 5 }}>
                {q.connections.map(function(conn, i) {
                  return (
                    <div key={i} style={{
                      color: C.text, fontSize: 11, lineHeight: 1.6,
                      padding: "6px 0",
                      borderBottom: i < q.connections.length - 1 ? "1px solid " + C.border : "none",
                      display: "flex", gap: 8,
                    }}>
                      <span style={{ color: C.cyan, flexShrink: 0 }}>&#8594;</span>
                      <span>{conn}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 6 }}>Linea de ataque</div>
              <div style={{ color: C.accent, fontSize: 12, lineHeight: 1.7, padding: "10px 12px", background: C.accent + "0a", borderRadius: 5, borderLeft: "3px solid " + C.accent }}>
                {q.attack}
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

export default function OpenQuestions() {
  const [openIds, setOpenIds] = useState({"Q1": true});

  function toggle(id) {
    setOpenIds(function(prev) {
      var next = {};
      for (var key in prev) { next[key] = prev[key]; }
      next[id] = !prev[id];
      return next;
    });
  }

  var alta = questions.filter(function(q) { return q.priority === "ALTA"; });
  var media = questions.filter(function(q) { return q.priority === "MEDIA"; });
  var baja = questions.filter(function(q) { return q.priority === "BAJA"; });

  return (
    <div style={{
      background: C.bg, color: C.text, minHeight: "100vh",
      fontFamily: "system-ui, sans-serif", padding: "20px 16px",
    }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>

        <div style={{ marginBottom: 20 }}>
          <div style={{ color: C.muted, fontSize: 10, textTransform: "uppercase", letterSpacing: 2 }}>
            Serie I - Substrate Scanning
          </div>
          <h1 style={{ margin: "4px 0 0", fontSize: 19, fontWeight: 700, color: C.text }}>
            Preguntas Abiertas
          </h1>
          <div style={{ color: C.muted, fontSize: 12, marginTop: 4 }}>
            6 preguntas | 2 alta prioridad | 2 media | 2 baja
          </div>
        </div>

        <div style={{
          display: "flex", gap: 8, marginBottom: 18, flexWrap: "wrap",
        }}>
          <div style={{ flex: 1, minWidth: 140, background: C.card, borderRadius: 6, padding: "10px 14px", border: "1px solid " + C.red + "30" }}>
            <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1 }}>Prioridad alta</div>
            <div style={{ fontFamily: "monospace", color: C.red, fontSize: 22, fontWeight: 700, marginTop: 2 }}>2</div>
            <div style={{ color: C.muted, fontSize: 10 }}>Q1: deficit universal, Q2: formula S(p)</div>
          </div>
          <div style={{ flex: 1, minWidth: 140, background: C.card, borderRadius: 6, padding: "10px 14px", border: "1px solid " + C.accent + "30" }}>
            <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1 }}>Prioridad media</div>
            <div style={{ fontFamily: "monospace", color: C.accent, fontSize: 22, fontWeight: 700, marginTop: 2 }}>2</div>
            <div style={{ color: C.muted, fontSize: 10 }}>Q3: gradiente, Q4: autocorrelacion</div>
          </div>
          <div style={{ flex: 1, minWidth: 140, background: C.card, borderRadius: 6, padding: "10px 14px", border: "1px solid " + C.border }}>
            <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1 }}>Prioridad baja</div>
            <div style={{ fontFamily: "monospace", color: C.muted, fontSize: 22, fontWeight: 700, marginTop: 2 }}>2</div>
            <div style={{ color: C.muted, fontSize: 10 }}>Q5: palindromos, Q6: delta-ratio</div>
          </div>
        </div>

        <div style={{ marginBottom: 8 }}>
          <div style={{ color: C.red, fontSize: 11, fontWeight: 600, letterSpacing: 0.5, marginBottom: 8 }}>PRIORIDAD ALTA</div>
          {alta.map(function(q) {
            return <QuestionCard key={q.id} q={q} isOpen={!!openIds[q.id]} onToggle={function() { toggle(q.id); }} />;
          })}
        </div>

        <div style={{ marginBottom: 8 }}>
          <div style={{ color: C.accent, fontSize: 11, fontWeight: 600, letterSpacing: 0.5, marginBottom: 8 }}>PRIORIDAD MEDIA</div>
          {media.map(function(q) {
            return <QuestionCard key={q.id} q={q} isOpen={!!openIds[q.id]} onToggle={function() { toggle(q.id); }} />;
          })}
        </div>

        <div style={{ marginBottom: 8 }}>
          <div style={{ color: C.muted, fontSize: 11, fontWeight: 600, letterSpacing: 0.5, marginBottom: 8 }}>PRIORIDAD BAJA</div>
          {baja.map(function(q) {
            return <QuestionCard key={q.id} q={q} isOpen={!!openIds[q.id]} onToggle={function() { toggle(q.id); }} />;
          })}
        </div>

        <div style={{
          marginTop: 16, padding: 14, background: C.card,
          borderRadius: 8, border: "1px solid " + C.cyan + "30",
        }}>
          <div style={{ color: C.cyan, fontSize: 11, fontWeight: 600, marginBottom: 6 }}>NEXT ACTION</div>
          <div style={{ color: C.text, fontSize: 12, lineHeight: 1.7 }}>
            Q1 y Q2 son la misma pregunta vista desde angulos distintos. La linea de ataque
            concreta: correlacionar v2(p-1) con |S - k/2| para half-reptend con p = 7 (mod 8).
            Si la correlacion es fuerte, el mecanismo es la profundidad 2-adica y conecta
            directamente con el paper de valuacion q-adica de Serie I.
          </div>
        </div>

        <div style={{ textAlign: "center", color: C.muted, fontSize: 10, padding: "14px 0 20px", fontFamily: "monospace" }}>
          Serie I | 6 preguntas abiertas | 2026-03-28
        </div>
      </div>
    </div>
  );
}
