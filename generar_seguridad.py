#!/usr/bin/env python3
"""Genera seguridad.json con el índice de seguridad por distrito de Madrid."""

import json
import pandas as pd

EXCEL = "/Users/ignacio/Downloads/212616-148-policia-estadisticas.xlsx"
OUTPUT = "/Users/ignacio/Sites/casa/seguridad.json"

EXCLUIR = {"SIN DISTRITO ASIGNADO", "TOTAL"}

PESOS = {
    "personas":   0.30,
    "patrimonio": 0.20,
    "drogas":     0.20,
    "armas":      0.25,
    "accidentes": 0.05,
}


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


def main():
    xl = pd.ExcelFile(EXCEL, engine="openpyxl")

    # --- SEGURIDAD ---
    df_seg = parse_hoja(xl, "SEGURIDAD")
    col_dist = df_seg.columns[0]
    df_seg[col_dist] = df_seg[col_dist].astype(str).str.strip()
    df_seg = df_seg[~df_seg[col_dist].isin(EXCLUIR)].copy()

    col_personas   = [c for c in df_seg.columns if "PERSONAS" in str(c).upper()][0]
    col_patrimonio = [c for c in df_seg.columns if "PATRIMONIO" in str(c).upper()][0]
    col_armas      = [c for c in df_seg.columns if "ARMAS" in str(c).upper()][0]
    col_ten_drogas = [c for c in df_seg.columns if "TENENCIA DE DROGAS" in str(c).upper()][0]
    col_con_drogas = [c for c in df_seg.columns if "CONSUMO DE DROGAS" in str(c).upper()][0]

    df_seg["personas"]   = pd.to_numeric(df_seg[col_personas],   errors="coerce").fillna(0)
    df_seg["patrimonio"] = pd.to_numeric(df_seg[col_patrimonio], errors="coerce").fillna(0)
    df_seg["armas"]      = pd.to_numeric(df_seg[col_armas],      errors="coerce").fillna(0)
    df_seg["drogas"]     = (
        pd.to_numeric(df_seg[col_ten_drogas], errors="coerce").fillna(0) +
        pd.to_numeric(df_seg[col_con_drogas], errors="coerce").fillna(0)
    )

    # --- ACCIDENTES ---
    df_acc = parse_hoja(xl, "ACCIDENTES")
    col_dist_acc = df_acc.columns[0]
    df_acc[col_dist_acc] = df_acc[col_dist_acc].astype(str).str.strip()
    df_acc = df_acc[~df_acc[col_dist_acc].isin(EXCLUIR)].copy()
    col_victimas = [c for c in df_acc.columns if "VICTIMAS" in str(c).upper() or "VÍCTIMAS" in str(c).upper()][0]
    df_acc["accidentes"] = pd.to_numeric(df_acc[col_victimas], errors="coerce").fillna(0)

    # Merge por nombre de distrito
    df = df_seg[[col_dist, "personas", "patrimonio", "armas", "drogas"]].copy()
    df = df.rename(columns={col_dist: "distrito"})
    df_acc_merge = df_acc[[col_dist_acc, "accidentes"]].rename(columns={col_dist_acc: "distrito"})
    df = df.merge(df_acc_merge, on="distrito", how="left")
    df["accidentes"] = df["accidentes"].fillna(0)

    # Normalizar cada métrica
    for col in ["personas", "patrimonio", "armas", "drogas", "accidentes"]:
        df[f"n_{col}"] = normalizar(df[col])

    # Índice de inseguridad (0=seguro, 1=inseguro)
    df["inseguridad"] = (
        df["n_personas"]   * PESOS["personas"] +
        df["n_patrimonio"] * PESOS["patrimonio"] +
        df["n_drogas"]     * PESOS["drogas"] +
        df["n_armas"]      * PESOS["armas"] +
        df["n_accidentes"] * PESOS["accidentes"]
    )

    # Índice de seguridad 0-10 (10=más seguro)
    df["indice"] = (10 - df["inseguridad"] * 10).round(1)

    # Percentiles para generar motivos
    rankings = {}
    for col in ["personas", "patrimonio", "armas", "drogas", "accidentes"]:
        rankings[col] = {
            "p25": df[col].quantile(0.25),
            "p75": df[col].quantile(0.75),
        }

    # Construir JSON
    resultado = []
    for _, row in df.sort_values("indice", ascending=False).iterrows():
        resultado.append({
            "distrito": row["distrito"],
            "indice": float(row["indice"]),
            "detalles": {
                "delitos_personas":    int(row["personas"]),
                "delitos_patrimonio":  int(row["patrimonio"]),
                "drogas":              int(row["drogas"]),
                "armas":               int(row["armas"]),
                "accidentes_victimas": int(row["accidentes"]),
            },
            "motivo": generar_motivo(row, rankings),
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"Generado {OUTPUT} con {len(resultado)} distritos\n")
    print(f"{'Distrito':<30} {'Índice':>6}  {'Motivo'}")
    print("-" * 90)
    for d in resultado:
        print(f"{d['distrito']:<30} {d['indice']:>6.1f}  {d['motivo'][:55]}")


if __name__ == "__main__":
    main()
