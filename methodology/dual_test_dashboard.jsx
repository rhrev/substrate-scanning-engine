import React, { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, Cell } from "recharts";

const C = {
  bg: "#090d12",
  card: "#111a25",
  cardAlt: "#172030",
  accent: "#d4a017",
  cyan: "#4db8c2",
  red: "#c94040",
  green: "#4a9e5c",
  magenta: "#a86cc1",
  text: "#cdd3da",
  muted: "#5e7080",
  border: "#1e3040",
  orange: "#d97a2b",
};

var v2StratData = [
  { v2: 1, n: 2583, density: 0.4947, exactZero: 50.1, negPct: 46.6, meanDev: -23.8, label: "v2=1" },
  { v2: 2, n: 1292, density: 0.5000, exactZero: 100.0, negPct: 0.0, meanDev: 0.0, label: "v2=2" },
  { v2: 3, n: 621, density: 0.4966, exactZero: 74.4, negPct: 17.4, meanDev: -1.3, label: "v2=3" },
  { v2: 4, n: 309, density: 0.4986, exactZero: 91.6, negPct: 4.5, meanDev: -0.3, label: "v2=4" },
  { v2: 5, n: 160, density: 0.4992, exactZero: 93.8, negPct: 3.8, meanDev: -0.07, label: "v2=5" },
  { v2: 6, n: 89, density: 0.5002, exactZero: 98.9, negPct: 0.0, meanDev: 0.05, label: "v2=6" },
  { v2: 7, n: 40, density: 0.5000, exactZero: 100.0, negPct: 0.0, meanDev: 0.0, label: "v2=7" },
  { v2: 8, n: 20, density: 0.5000, exactZero: 100.0, negPct: 0.0, meanDev: 0.0, label: "v2=8" },
];

var torusStratData = [
  { v2: 1, n: 2514, phase: 0.006521, amp: 1.000487, coh: 0.999915, label: "v2=1" },
  { v2: 2, n: 1262, phase: 0.006872, amp: 1.000408, coh: 0.999846, label: "v2=2" },
  { v2: 3, n: 604, phase: 0.006344, amp: 0.999837, coh: 0.999985, label: "v2=3" },
  { v2: 4, n: 301, phase: 0.006514, amp: 1.000870, coh: 0.999702, label: "v2=4" },
  { v2: 5, n: 155, phase: 0.006588, amp: 0.999899, coh: 0.999997, label: "v2=5" },
  { v2: 6, n: 89, phase: 0.006642, amp: 0.999128, coh: 1.000000, label: "v2=6" },
];

var dualTestData = [
  { pair: "v2 -> |S-k/2|", rho: -0.432, p: "10^-226", chA: true, chB: false, sig: true },
  { pair: "v2 -> density", rho: 0.391, p: "10^-187", chA: true, chB: false, sig: true },
  { pair: "v2 -> amplitude", rho: -0.005, p: "0.70", chA: false, chB: true, sig: false },
  { pair: "v2 -> |phase|", rho: 0.006, p: "0.65", chA: false, chB: true, sig: false },
  { pair: "v2 -> coherence", rho: 0.005, p: "0.70", chA: false, chB: true, sig: false },
  { pair: "|S-k/2| <-> |phase|", rho: -0.036, p: "0.01", chA: true, chB: true, sig: false },
  { pair: "|S-k/2| <-> amp", rho: 0.001, p: "0.97", chA: true, chB: true, sig: false },
  { pair: "density <-> |phase|", rho: -0.032, p: "0.02", chA: true, chB: true, sig: false },
];

function Panel({ title, children, border }) {
  return (
    <div style={{
      background: C.card, borderRadius: 8, padding: "16px 18px",
      border: "1px solid " + (border || C.border), marginBottom: 14,
    }}>
      <h3 style={{ color: C.accent, margin: "0 0 12px 0", fontSize: 13, fontWeight: 600, letterSpacing: 0.4 }}>{title}</h3>
      {children}
    </div>
  );
}

function Stat({ label, value, sub, color }) {
  return (
    <div style={{
      background: C.cardAlt, borderRadius: 6, padding: "10px 14px",
      border: "1px solid " + (color ? color + "40" : C.border),
      flex: 1, minWidth: 120,
    }}>
      <div style={{ color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: 1.2 }}>{label}</div>
      <div style={{ fontFamily: "monospace", color: color || C.text, fontSize: 18, fontWeight: 700, marginTop: 3 }}>{value}</div>
      {sub && <div style={{ color: C.muted, fontSize: 10, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div style={{ background: "#070a0f", border: "1px solid " + C.border, borderRadius: 5, padding: "6px 10px", fontSize: 11, fontFamily: "monospace" }}>
      <div style={{ color: C.text, fontWeight: 600, marginBottom: 3 }}>{label}</div>
      {payload.map(function(p, i) {
        return <div key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === "number" ? p.value.toFixed(6) : p.value}</div>;
      })}
    </div>
  );
}

export default function DualTestDashboard() {
  var [tab, setTab] = useState("verdict");

  var tabs = [
    { key: "verdict", label: "Veredicto" },
    { key: "channelA", label: "Canal A (Digitos)" },
    { key: "channelB", label: "Canal B (Toro)" },
    { key: "cross", label: "Cross-Channel" },
  ];

  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", fontFamily: "system-ui, sans-serif", padding: "20px 16px" }}>
      <div style={{ maxWidth: 780, margin: "0 auto" }}>

        <div style={{ marginBottom: 18 }}>
          <div style={{ color: C.muted, fontSize: 10, textTransform: "uppercase", letterSpacing: 2 }}>
            Serie I - Two Windows, One Object - Test Dual
          </div>
          <h1 style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 700 }}>
            v2(p-1) como Predictor Cross-Channel
          </h1>
          <div style={{ color: C.muted, fontSize: 12, marginTop: 4 }}>
            5,132 primos | Canal A: digit-sum | Canal B: producto de Euler parcial | gamma1
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 14, flexWrap: "wrap" }}>
          <Stat label="Canal A: v2->|dev|" value="-0.432" sub="p = 10^-226" color={C.green} />
          <Stat label="Canal B: v2->amp" value="-0.005" sub="p = 0.70" color={C.red} />
          <Stat label="Cross A<->B" value="0.001" sub="p = 0.97" color={C.red} />
          <Stat label="Veredicto" value="ORTOGONAL" sub="canales independientes" color={C.orange} />
        </div>

        <div style={{ display: "flex", gap: 3, marginBottom: 14, flexWrap: "wrap" }}>
          {tabs.map(function(t) {
            return (
              <button key={t.key} onClick={function() { setTab(t.key); }} style={{
                background: tab === t.key ? C.accent : C.cardAlt,
                color: tab === t.key ? "#000" : C.muted,
                border: "1px solid " + (tab === t.key ? C.accent : C.border),
                borderRadius: 5, padding: "7px 12px", cursor: "pointer",
                fontSize: 11, fontWeight: tab === t.key ? 700 : 400,
              }}>
                {t.label}
              </button>
            );
          })}
        </div>

        {tab === "verdict" && (
          <div>
            <Panel title="VEREDICTO DEL TEST DUAL" border={C.orange + "60"}>
              <div style={{ background: C.orange + "12", border: "2px solid " + C.orange + "40", borderRadius: 8, padding: 16, marginBottom: 14 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: C.orange, marginBottom: 8 }}>
                  CONEXION PARCIAL: v2(p-1) PREDICE CANAL A, NO CANAL B
                </div>
                <div style={{ fontSize: 12, lineHeight: 1.7 }}>
                  <div style={{ marginBottom: 8 }}>
                    <strong style={{ color: C.green }}>Canal A (digit-sum):</strong> v2(p-1) es un predictor
                    fuerte de |S - k/2| con rho = -0.43, p = 10^-226. Primos con v2 alto tienen
                    S = k/2 exacto; primos con v2 = 1 tienen deficit sistematico. El mecanismo es
                    algebraico: v2 determina si Midy aplica.
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <strong style={{ color: C.red }}>Canal B (toroidal):</strong> v2(p-1) tiene rho = -0.005,
                    p = 0.70 contra la amplitud del factor de Euler. Completamente null. El toro
                    no ve la estructura 2-adica de p-1.
                  </div>
                  <div>
                    <strong style={{ color: C.red }}>Cross-channel:</strong> |S - k/2| vs amplitud toroidal:
                    rho = 0.001, p = 0.97. Los canales son ortogonales.
                    La nota "Two Windows" sobreestima la conexion.
                  </div>
                </div>
              </div>

              <div style={{ fontSize: 12, lineHeight: 1.7, padding: "12px 14px", background: C.cardAlt, borderRadius: 6, marginBottom: 12 }}>
                <strong style={{ color: C.accent }}>Colapso de Q1:</strong> Para half-reptend p = 7 (mod 8),
                v2(p-1) = 1 para TODOS (porque p-1 = 6 mod 8). No hay variacion dentro de la
                subclase. El "ataque propuesto" en la nota Two Windows y en las Preguntas Abiertas
                es inoperable para la pregunta que motivaba.
              </div>

              <div style={{ fontSize: 12, lineHeight: 1.7, padding: "12px 14px", background: C.cardAlt, borderRadius: 6 }}>
                <strong style={{ color: C.accent }}>Hallazgo genuino (no anticipado):</strong> La
                estratificacion por v2(p-1) sobre TODOS los primos revela una jerarquia limpia:
                <div style={{ fontFamily: "monospace", marginTop: 8, fontSize: 11, lineHeight: 1.8 }}>
                  <div><span style={{ color: C.red }}>v2=1:</span> density = 0.4947, 50% Midy exacto, 47% deficit</div>
                  <div><span style={{ color: C.green }}>v2=2:</span> density = 0.5000, 100% Midy exacto</div>
                  <div><span style={{ color: C.cyan }}>v2=3:</span> density = 0.4966, 74% Midy exacto</div>
                  <div><span style={{ color: C.cyan }}>v2=4:</span> density = 0.4986, 92% Midy exacto</div>
                  <div><span style={{ color: C.green }}>v2=5+:</span> density -> 0.5000, ~94-100% Midy exacto</div>
                </div>
                <div style={{ marginTop: 8, color: C.muted }}>
                  v2 = 2 es el caso especial: 100% Midy, siempre. v2 = 1 es el peor caso.
                  v2 >= 3 converge monotonamente a 0.5. El patron NO es monotono en v2
                  — es {"{1: malo, 2: perfecto, 3+: convergente}"}.
                </div>
              </div>
            </Panel>

            <Panel title="REVISION DE TWO WINDOWS">
              <div style={{ fontSize: 12, lineHeight: 1.7 }}>
                <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                  <span style={{ color: C.green, flexShrink: 0 }}>OK</span>
                  <div>S1 (objeto compartido): correcto. Ambos canales leen (Z/pZ)*.</div>
                </div>
                <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                  <span style={{ color: C.green, flexShrink: 0 }}>OK</span>
                  <div>S7 (eficiencia de muestreo): confirmado. Ambos necesitan pocos primos.</div>
                </div>
                <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                  <span style={{ color: C.orange, flexShrink: 0 }}>!!</span>
                  <div>S2-S3 (Q1/Q2 como toro): el mecanismo propuesto (v2) falla en el toro.
                  La conexion f(b) es formal, no operativa.</div>
                </div>
                <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                  <span style={{ color: C.red, flexShrink: 0 }}>NO</span>
                  <div>S8 (puente f(b)): la pregunta abierta sobre regimen cuadratico no tiene
                  soporte empirico. Los canales son ortogonales.</div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <span style={{ color: C.orange, flexShrink: 0 }}>!!</span>
                  <div>S9 (estatus epistemico): necesita downgrade. "Structural" solo aplica
                  al objeto compartido; las correspondencias Q-a-Q son analogicas en el mejor
                  caso, y refutadas para el predictor v2.</div>
                </div>
              </div>
            </Panel>
          </div>
        )}

        {tab === "channelA" && (
          <div>
            <Panel title="CANAL A: DENSIDAD DEL PERIODO POR v2(p-1)">
              <div style={{ color: C.muted, fontSize: 11, marginBottom: 10 }}>
                v2(p-1) predice la densidad del periodo con rho = +0.39 (p = 10^-187).
                v2 = 2 es perfecto; v2 = 1 es deficitario.
              </div>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={v2StratData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                  <XAxis dataKey="label" stroke={C.muted} tick={{ fontSize: 10 }} />
                  <YAxis domain={[0.493, 0.502]} stroke={C.muted} tick={{ fontSize: 10, fontFamily: "monospace" }} />
                  <Tooltip content={CustomTooltip} />
                  <Bar dataKey="density" name="Densidad">
                    {v2StratData.map(function(d, i) {
                      var fill = d.density >= 0.4999 ? C.green : d.density >= 0.498 ? C.cyan : d.density >= 0.496 ? C.orange : C.red;
                      return <Cell key={i} fill={fill} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="PORCENTAJE MIDY EXACTO (S = k/2) POR v2">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={v2StratData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                  <XAxis dataKey="label" stroke={C.muted} tick={{ fontSize: 10 }} />
                  <YAxis domain={[0, 105]} stroke={C.muted} tick={{ fontSize: 10 }}
                    tickFormatter={function(v) { return v + "%"; }} />
                  <Tooltip content={CustomTooltip} />
                  <Bar dataKey="exactZero" name="% Midy exacto">
                    {v2StratData.map(function(d, i) {
                      var fill = d.exactZero >= 99 ? C.green : d.exactZero >= 90 ? C.cyan : d.exactZero >= 70 ? C.orange : C.red;
                      return <Cell key={i} fill={fill} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ marginTop: 10, fontSize: 11, color: C.muted, padding: "8px 10px", background: C.cardAlt, borderRadius: 5 }}>
                <strong style={{ color: C.accent }}>Patron no monotono:</strong> v2=2 da 100% (no v2=1),
                luego baja a 74% en v2=3 y sube monotonamente. El caso v2=2 es especial:
                p = 1 (mod 4) pero p != 1 (mod 8), y ord2(p) siempre tiene k par
                cuando v2(p-1) = 2.
              </div>
            </Panel>
          </div>
        )}

        {tab === "channelB" && (
          <Panel title="CANAL B: CANTIDADES TOROIDALES POR v2(p-1)">
            <div style={{ color: C.muted, fontSize: 11, marginBottom: 10 }}>
              Todas las cantidades toroidales son PLANAS en v2. No hay senal.
            </div>
            <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse", fontFamily: "monospace" }}>
              <thead>
                <tr style={{ color: C.accent, borderBottom: "1px solid " + C.border }}>
                  <th style={{ textAlign: "left", padding: "5px 8px" }}>v2</th>
                  <th style={{ textAlign: "right", padding: "5px 8px" }}>n</th>
                  <th style={{ textAlign: "right", padding: "5px 8px" }}>|phase|</th>
                  <th style={{ textAlign: "right", padding: "5px 8px" }}>amplitude</th>
                  <th style={{ textAlign: "right", padding: "5px 8px" }}>coherence</th>
                </tr>
              </thead>
              <tbody>
                {torusStratData.map(function(d) {
                  return (
                    <tr key={d.v2} style={{ borderBottom: "1px solid " + C.border + "22" }}>
                      <td style={{ padding: "4px 8px", color: C.text }}>{d.v2}</td>
                      <td style={{ padding: "4px 8px", textAlign: "right", color: C.muted }}>{d.n}</td>
                      <td style={{ padding: "4px 8px", textAlign: "right", color: C.red }}>{d.phase.toFixed(6)}</td>
                      <td style={{ padding: "4px 8px", textAlign: "right", color: C.red }}>{d.amp.toFixed(6)}</td>
                      <td style={{ padding: "4px 8px", textAlign: "right", color: C.red }}>{d.coh.toFixed(6)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div style={{ marginTop: 12, padding: 12, background: C.cardAlt, borderRadius: 5, fontSize: 12, lineHeight: 1.7 }}>
              <strong style={{ color: C.red }}>Diagnostico:</strong> Las tres columnas (fase, amplitud, coherencia)
              son constantes a 3 digitos significativos a traves de todos los valores de v2.
              El producto de Euler parcial en s = 1/2 + i*gamma1 no ve la estructura 2-adica
              de p-1. El factor (1 - p^-s) depende de p^-sigma y ln(p)*t, ninguno de los cuales
              codifica la factorizacion de p-1.
              <div style={{ marginTop: 8, color: C.accent }}>
                Esto es esperado en retrospectiva: p^-s = exp(-s*ln(p)) es una funcion
                de ln(p), no de la factorizacion de p-1. La estructura multiplicativa de p-1
                es invisible para el logaritmo.
              </div>
            </div>
          </Panel>
        )}

        {tab === "cross" && (
          <Panel title="TABLA COMPLETA DE CORRELACIONES CROSS-CHANNEL">
            <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse", fontFamily: "monospace" }}>
              <thead>
                <tr style={{ color: C.accent, borderBottom: "1px solid " + C.border }}>
                  <th style={{ textAlign: "left", padding: "6px 8px" }}>Par</th>
                  <th style={{ textAlign: "right", padding: "6px 8px" }}>rho</th>
                  <th style={{ textAlign: "right", padding: "6px 8px" }}>p-value</th>
                  <th style={{ textAlign: "center", padding: "6px 8px" }}>Canal</th>
                  <th style={{ textAlign: "center", padding: "6px 8px" }}>Senal</th>
                </tr>
              </thead>
              <tbody>
                {dualTestData.map(function(d) {
                  var chanLabel = d.chA && d.chB ? "A<->B" : d.chA ? "v2->A" : "v2->B";
                  return (
                    <tr key={d.pair} style={{ borderBottom: "1px solid " + C.border + "22" }}>
                      <td style={{ padding: "5px 8px", color: C.text, fontSize: 10 }}>{d.pair}</td>
                      <td style={{ padding: "5px 8px", textAlign: "right", color: d.sig ? C.green : C.red, fontWeight: d.sig ? 700 : 400 }}>
                        {d.rho > 0 ? "+" : ""}{d.rho.toFixed(3)}
                      </td>
                      <td style={{ padding: "5px 8px", textAlign: "right", color: C.muted }}>{d.p}</td>
                      <td style={{ padding: "5px 8px", textAlign: "center", color: C.cyan }}>{chanLabel}</td>
                      <td style={{ padding: "5px 8px", textAlign: "center", color: d.sig ? C.green : C.red }}>
                        {d.sig ? "SI" : "NO"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div style={{ marginTop: 12, padding: 12, background: C.cardAlt, borderRadius: 5, fontSize: 12, lineHeight: 1.7 }}>
              <strong style={{ color: C.orange }}>Lectura:</strong> v2(p-1) es un predictor potente
              (rho = -0.43) para el canal de digit-sum, pero tiene rho {"<"} 0.01 para TODAS las
              cantidades toroidales. Las correlaciones cross-channel directas (filas A{"<->"}B)
              son todas rho {"<"} 0.04. Los canales son funcionalmente independientes.
              <div style={{ marginTop: 8, color: C.muted }}>
                Esto NO invalida que ambos lean (Z/pZ)* — pero leen subestructuras
                ortogonales de ese grupo. El canal A lee la estructura de los subgrupos
                (ordenes, cuadrados, Midy). El canal B lee las frecuencias logaritmicas
                (fases, amplitudes). No comparten informacion.
              </div>
            </div>
          </Panel>
        )}

        <Panel title="ACTUALIZACION DE PREGUNTAS ABIERTAS">
          <div style={{ fontSize: 12, lineHeight: 1.7 }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
              <span style={{ color: C.red, flexShrink: 0, fontWeight: 700, fontFamily: "monospace" }}>Q1</span>
              <div>
                <strong style={{ color: C.red }}>CERRADA (ataque propuesto inoperable).</strong>{" "}
                v2(p-1) = 1 para todos p = 7 (mod 8). No hay variacion.
                Pero el deficit S {"<"} k/2 persiste universalmente — necesita un nuevo mecanismo
                explicativo. Candidato: la distribucion de los residuos cuadraticos de 2 en (Z/pZ)*
                cuando k es impar.
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
              <span style={{ color: C.accent, flexShrink: 0, fontWeight: 700, fontFamily: "monospace" }}>Q2</span>
              <div>
                <strong style={{ color: C.accent }}>REFORMULADA.</strong>{" "}
                Para todos los primos, v2(p-1) predice la densidad con un patron no monotono:
                {"{1: deficit, 2: perfecto, 3+: convergente}"}. La formula cerrada para S(p)
                debe incorporar v2(p-1) como variable, no solo p mod 8.
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <span style={{ color: C.red, flexShrink: 0, fontWeight: 700, fontFamily: "monospace" }}>S8</span>
              <div>
                <strong style={{ color: C.red }}>REFUTADO.</strong>{" "}
                El puente f(b) entre los dos programas no tiene soporte empirico.
                Los canales son ortogonales. La nota Two Windows necesita revision:
                S1 y S7 se mantienen; S2-S6 deben clasificarse como analogias, no conexiones
                estructurales; S8 debe eliminarse o marcarse como falsificado.
              </div>
            </div>
          </div>
        </Panel>

        <div style={{ textAlign: "center", color: C.muted, fontSize: 10, padding: "8px 0 20px", fontFamily: "monospace" }}>
          Serie I | Test Dual | v2 predice A, no B | canales ortogonales | 2026-03-28
        </div>
      </div>
    </div>
  );
}
