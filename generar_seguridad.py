#!/usr/bin/env python3
"""Genera seguridad.json con el índice de seguridad por distrito de Madrid.

Uso:
    python generar_seguridad.py --mes 2025-04
    python generar_seguridad.py --mes 2025-05 --excel /ruta/otro.xlsx
"""

import argparse
import json
import re
import sys

import pandas as pd

EXCEL  = "/Users/ignacio/Downloads/212616-148-policia-estadisticas.xlsx"
OUTPUT = "/Users/ignacio/Sites/casa/seguridad.json"

EXCLUIR = {"SIN DISTRITO ASIGNADO", "TOTAL"}

PESOS = {
    "personas":   0.30,
    "patrimonio": 0.20,
    "drogas":     0.20,
    "armas":      0.25,
    "accidentes": 0.05,
}

MES_BACKFILL = "2026-04"   # mes asignado a datos legacy sin campo `meses`


# ---------------------------------------------------------------------------
# Helpers compartidos
# ---------------------------------------------------------------------------

def parse_hoja(xl, nombre, header_keyword="DISTRITO"):
    df = xl.parse(nombre, header=None)
    header_row = next(
        i for i, row in df.iterrows()
        if any(header_keyword in str(v).upper() for v in row)
    )
    df.columns = df.iloc[header_row]
    return df.iloc[header_row + 1:].reset_index(drop=True)


def normalizar(serie):
    mn, mx = serie.min(), serie.max()
    if mx == mn:
        return serie * 0.0
    return (serie - mn) / (mx - mn)


def calcular_indice(df):
    """Normaliza las 5 métricas y devuelve el índice de seguridad 0-10."""
    for col in ["personas", "patrimonio", "armas", "drogas", "accidentes"]:
        df[f"n_{col}"] = normalizar(df[col])
    df["inseguridad"] = (
        df["n_personas"]   * PESOS["personas"] +
        df["n_patrimonio"] * PESOS["patrimonio"] +
        df["n_drogas"]     * PESOS["drogas"] +
        df["n_armas"]      * PESOS["armas"] +
        df["n_accidentes"] * PESOS["accidentes"]
    )
    df["indice"] = (10 - df["inseguridad"] * 10).round(1)
    return df


def generar_motivo(row, rankings):
    """Genera 1-2 frases explicando la puntuación del distrito."""
    partes = []
    if row["personas"] >= rankings["personas"]["p75"]:
        partes.append(f"alta criminalidad contra personas ({int(row['personas'])} casos)")
    if row["patrimonio"] >= rankings["patrimonio"]["p75"]:
        partes.append(f"muchos delitos contra el patrimonio ({int(row['patrimonio'])} casos)")
    if row["drogas"] >= rankings["drogas"]["p75"]:
        partes.append(f"elevada actividad relacionada con drogas ({int(row['drogas'])} casos)")
    if row["armas"] >= rankings["armas"]["p75"]:
        partes.append(f"alta tenencia de armas ({int(row['armas'])} casos)")
    if row["accidentes"] >= rankings["accidentes"]["p75"]:
        partes.append(f"muchos accidentes con víctimas ({int(row['accidentes'])})")

    positivos = []
    if row["personas"] <= rankings["personas"]["p25"]:
        positivos.append("baja criminalidad violenta")
    if row["patrimonio"] <= rankings["patrimonio"]["p25"]:
        positivos.append("pocos delitos contra el patrimonio")
    if row["drogas"] <= rankings["drogas"]["p25"]:
        positivos.append("escasa actividad con drogas")

    if partes:
        texto = "Destaca por: " + ", ".join(partes) + "."
    elif positivos:
        texto = "Distrito tranquilo con " + " y ".join(positivos) + "."
    else:
        texto = "Niveles intermedios en todas las categorías."

    if positivos and partes:
        texto += " Puntos positivos: " + " y ".join(positivos) + "."
    return texto


def calcular_rankings(df):
    rankings = {}
    for col in ["personas", "patrimonio", "armas", "drogas", "accidentes"]:
        rankings[col] = {"p25": df[col].quantile(0.25), "p75": df[col].quantile(0.75)}
    return rankings


# ---------------------------------------------------------------------------
# Paso 1: leer el Excel y calcular datos del mes
# ---------------------------------------------------------------------------

def parse_and_compute_month(xl):
    """Parsea el Excel y devuelve dict[distrito → {detalles, indice, motivo}]."""
    # Seguridad
    df_seg = parse_hoja(xl, "SEGURIDAD")
    col_dist = df_seg.columns[0]
    df_seg[col_dist] = df_seg[col_dist].astype(str).str.strip()
    df_seg = df_seg[~df_seg[col_dist].isin(EXCLUIR)].copy()

    col_personas   = [c for c in df_seg.columns if "PERSONAS"          in str(c).upper()][0]
    col_patrimonio = [c for c in df_seg.columns if "PATRIMONIO"        in str(c).upper()][0]
    col_armas      = [c for c in df_seg.columns if "ARMAS"             in str(c).upper()][0]
    col_ten_drogas = [c for c in df_seg.columns if "TENENCIA DE DROGAS" in str(c).upper()][0]
    col_con_drogas = [c for c in df_seg.columns if "CONSUMO DE DROGAS"  in str(c).upper()][0]

    df_seg["personas"]   = pd.to_numeric(df_seg[col_personas],   errors="coerce").fillna(0)
    df_seg["patrimonio"] = pd.to_numeric(df_seg[col_patrimonio], errors="coerce").fillna(0)
    df_seg["armas"]      = pd.to_numeric(df_seg[col_armas],      errors="coerce").fillna(0)
    df_seg["drogas"]     = (
        pd.to_numeric(df_seg[col_ten_drogas], errors="coerce").fillna(0) +
        pd.to_numeric(df_seg[col_con_drogas], errors="coerce").fillna(0)
    )

    # Accidentes
    df_acc = parse_hoja(xl, "ACCIDENTES")
    col_dist_acc = df_acc.columns[0]
    df_acc[col_dist_acc] = df_acc[col_dist_acc].astype(str).str.strip()
    df_acc = df_acc[~df_acc[col_dist_acc].isin(EXCLUIR)].copy()
    col_victimas = [c for c in df_acc.columns if "VICTIMAS" in str(c).upper() or "VÍCTIMAS" in str(c).upper()][0]
    df_acc["accidentes"] = pd.to_numeric(df_acc[col_victimas], errors="coerce").fillna(0)

    df = df_seg[[col_dist, "personas", "patrimonio", "armas", "drogas"]].rename(columns={col_dist: "distrito"})
    df = df.merge(
        df_acc[[col_dist_acc, "accidentes"]].rename(columns={col_dist_acc: "distrito"}),
        on="distrito", how="left"
    )
    df["accidentes"] = df["accidentes"].fillna(0)

    df = calcular_indice(df.copy())
    rankings = calcular_rankings(df)

    resultado = {}
    for _, row in df.iterrows():
        resultado[row["distrito"]] = {
            "detalles": {
                "delitos_personas":    int(row["personas"]),
                "delitos_patrimonio":  int(row["patrimonio"]),
                "drogas":              int(row["drogas"]),
                "armas":               int(row["armas"]),
                "accidentes_victimas": int(row["accidentes"]),
            },
            "indice": float(row["indice"]),
            "motivo": generar_motivo(row, rankings),
        }
    return resultado


# ---------------------------------------------------------------------------
# Paso 2: cargar JSON existente
# ---------------------------------------------------------------------------

def load_existing(path):
    """Lee seguridad.json y devuelve dict[distrito → entry]. Migra datos legacy."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}

    existing = {}
    for entry in data:
        # Migración automática: datos sin campo `meses` se asignan a MES_BACKFILL
        if "meses" not in entry:
            entry["meses"] = {
                MES_BACKFILL: {
                    "detalles": entry["detalles"],
                    "indice":   entry["indice"],
                    "motivo":   entry["motivo"],
                }
            }
        existing[entry["distrito"]] = entry
    return existing


# ---------------------------------------------------------------------------
# Paso 3: recalcular agregados desde todos los meses
# ---------------------------------------------------------------------------

def recalculate_aggregates(existing):
    """Recalcula indice/detalles/motivo top-level como media de todos los meses."""
    METRICAS = ["delitos_personas", "delitos_patrimonio", "drogas", "armas", "accidentes_victimas"]

    # Construir DataFrame de medias
    rows = []
    for distrito, entry in existing.items():
        meses = entry["meses"]
        n = len(meses)
        medias = {m: sum(mes["detalles"][m] for mes in meses.values()) / n for m in METRICAS}
        rows.append({
            "distrito":   distrito,
            "personas":   medias["delitos_personas"],
            "patrimonio": medias["delitos_patrimonio"],
            "drogas":     medias["drogas"],
            "armas":      medias["armas"],
            "accidentes": medias["accidentes_victimas"],
        })

    df = pd.DataFrame(rows)
    df = calcular_indice(df.copy())
    rankings = calcular_rankings(df)

    resultado = []
    for _, row in df.sort_values("indice", ascending=False).iterrows():
        distrito = row["distrito"]
        entry    = existing[distrito]
        resultado.append({
            "distrito": distrito,
            "indice":   float(row["indice"]),
            "detalles": {
                "delitos_personas":    round(row["personas"]),
                "delitos_patrimonio":  round(row["patrimonio"]),
                "drogas":              round(row["drogas"]),
                "armas":               round(row["armas"]),
                "accidentes_victimas": round(row["accidentes"]),
            },
            "motivo": generar_motivo(row, rankings),
            "meses":  dict(sorted(entry["meses"].items())),  # orden cronológico
        })
    return resultado


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Genera seguridad.json con soporte multi-mes.")
    parser.add_argument("--mes",   required=True, help="Mes del Excel en formato YYYY-MM (ej: 2025-05)")
    parser.add_argument("--excel", default=EXCEL,  help="Ruta al Excel de estadísticas policiales")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}", args.mes):
        print(f"Error: --mes debe tener formato YYYY-MM, se recibió '{args.mes}'", file=sys.stderr)
        sys.exit(1)

    xl = pd.ExcelFile(args.excel, engine="openpyxl")

    print(f"Procesando mes {args.mes} desde {args.excel}…")
    new_month_data = parse_and_compute_month(xl)

    existing = load_existing(OUTPUT)

    # Merge: añadir/sobreescribir el mes en cada distrito
    for distrito, mes_data in new_month_data.items():
        if distrito not in existing:
            existing[distrito] = {"distrito": distrito, "meses": {}}
        existing[distrito]["meses"][args.mes] = mes_data

    resultado = recalculate_aggregates(existing)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    n_meses = len(next(iter(resultado))["meses"]) if resultado else 0
    print(f"\nGenerado {OUTPUT} — {len(resultado)} distritos, {n_meses} mes(es) acumulado(s)\n")
    print(f"{'Distrito':<30} {'Índice':>6}  {'Meses':<12}  {'Motivo'}")
    print("-" * 100)
    for d in resultado:
        meses_str = ", ".join(sorted(d["meses"].keys()))
        print(f"{d['distrito']:<30} {d['indice']:>6.1f}  {meses_str:<12}  {d['motivo'][:50]}")


if __name__ == "__main__":
    main()
