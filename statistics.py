"""
STATlab - Motor estadístico completo.
"""

import pandas as pd
import numpy as np
from scipy import stats
from database import get_variable_data, get_dataframe
import json


def descriptivos(df, variable):
    """Estadísticos descriptivos de una variable numérica."""
    datos = df[variable].dropna()
    
    q1, q3 = datos.quantile(0.25), datos.quantile(0.75)
    
    return {
        "n": len(datos),
        "nulos": df[variable].isna().sum(),
        "media": round(float(datos.mean()), 4),
        "mediana": round(float(datos.median()), 4),
        "moda": datos.mode().tolist() if not datos.mode().empty else None,
        "desviacion_estandar": round(float(datos.std()), 4),
        "varianza": round(float(datos.var()), 4),
        "minimo": round(float(datos.min()), 4),
        "maximo": round(float(datos.max()), 4),
        "rango": round(float(datos.max() - datos.min()), 4),
        "q1": round(float(q1), 4),
        "q3": round(float(q3), 4),
        "iqr": round(float(q3 - q1), 4),
        "asimetria": round(float(datos.skew()), 4),
        "curtosis": round(float(datos.kurtosis()), 4),
        "error_estandar": round(float(datos.std() / np.sqrt(len(datos))), 4),
        "ic_95_inf": round(float(datos.mean() - 1.96 * datos.std() / np.sqrt(len(datos))), 4),
        "ic_95_sup": round(float(datos.mean() + 1.96 * datos.std() / np.sqrt(len(datos))), 4),
    }


def frecuencia_categorica(df, variable):
    """Tabla de frecuencias para variable categórica."""
    datos = df[variable].dropna()
    conteo = datos.value_counts()
    total = len(datos)
    
    return [
        {
            "categoria": str(cat),
            "frecuencia": int(conteo[cat]),
            "porcentaje": round(float(conteo[cat] / total * 100), 2),
            "porcentaje_acumulado": round(float(conteo[:i+1].sum() / total * 100), 2),
        }
        for i, cat in enumerate(conteo.index)
    ]


def normalidad(df, variable):
    """Prueba de normalidad."""
    datos = df[variable].dropna()
    
    if len(datos) <= 5000:
        stat, p = stats.shapiro(datos)
        test = "Shapiro-Wilk"
    else:
        stat, p = stats.kstest(datos, 'norm', args=(datos.mean(), datos.std()))
        test = "Kolmogorov-Smirnov"
    
    return {
        "test": test,
        "estadistico": round(float(stat), 4),
        "p_valor": round(float(p), 4),
        "es_normal": p > 0.05,
        "interpretacion": "Los datos siguen una distribución normal" if p > 0.05 else "Los datos NO siguen una distribución normal"
    }


def comparar_dos_grupos(df, var_num, var_cat, test="ttest"):
    """Compara variable numérica entre dos grupos."""
    grupos = df[var_cat].dropna().unique()
    
    if len(grupos) != 2:
        return {"error": f"Se necesitan 2 grupos. {var_cat} tiene {len(grupos)}."}
    
    g1 = df[df[var_cat] == grupos[0]][var_num].dropna()
    g2 = df[df[var_cat] == grupos[1]][var_num].dropna()
    
    if test == "ttest":
        stat, p = stats.ttest_ind(g1, g2)
        test_name = "t-test independiente"
    elif test == "mannwhitney":
        stat, p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
        test_name = "Mann-Whitney U"
    
    return {
        "test": test_name,
        "grupo_1": str(grupos[0]),
        "grupo_2": str(grupos[1]),
        "n_1": len(g1),
        "n_2": len(g2),
        "media_1": round(float(g1.mean()), 4),
        "media_2": round(float(g2.mean()), 4),
        "mediana_1": round(float(g1.median()), 4),
        "mediana_2": round(float(g2.median()), 4),
        "estadistico": round(float(stat), 4),
        "p_valor": round(float(p), 4),
        "significativo": p <= 0.05,
        "diferencia_medias": round(float(g1.mean() - g2.mean()), 4),
    }


def anova(df, var_num, var_cat):
    """ANOVA de una variable numérica por grupos."""
    grupos = df[var_cat].dropna().unique()
    muestras = [df[df[var_cat] == g][var_num].dropna().values for g in grupos]
    
    f_stat, p = stats.f_oneway(*muestras)
    
    return {
        "test": "ANOVA one-way",
        "grupos": [str(g) for g in grupos],
        "n_por_grupo": [len(m) for m in muestras],
        "medias_por_grupo": {str(g): round(float(m.mean()), 4) for g, m in zip(grupos, muestras)},
        "estadistico_F": round(float(f_stat), 4),
        "p_valor": round(float(p), 4),
        "significativo": p <= 0.05,
    }


def correlacion(df, var1, var2, metodo="pearson"):
    """Correlación entre dos variables numéricas."""
    mask = df[[var1, var2]].dropna().index
    x = df.loc[mask, var1]
    y = df.loc[mask, var2]
    
    if metodo == "pearson":
        r, p = stats.pearsonr(x, y)
        test = "Pearson"
    elif metodo == "spearman":
        r, p = stats.spearmanr(x, y)
        test = "Spearman"
    
    fuerza = (
        "muy débil" if abs(r) < 0.2 else
        "débil" if abs(r) < 0.4 else
        "moderada" if abs(r) < 0.6 else
        "fuerte" if abs(r) < 0.8 else
        "muy fuerte"
    )
    
    return {
        "test": f"Correlación de {test}",
        "coeficiente": round(float(r), 4),
        "r_cuadrado": round(float(r**2), 4),
        "p_valor": round(float(p), 4),
        "significativo": p <= 0.05,
        "fuerza": fuerza,
        "direccion": "positiva" if r > 0 else "negativa",
        "n": len(mask),
    }


def regresion_lineal(df, var_y, var_x):
    """Regresión lineal simple."""
    mask = df[[var_x, var_y]].dropna().index
    x = df.loc[mask, var_x]
    y = df.loc[mask, var_y]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    return {
        "ecuacion": f"Y = {intercept:.4f} + {slope:.4f} * X",
        "intercepto": round(float(intercept), 4),
        "pendiente": round(float(slope), 4),
        "r_cuadrado": round(float(r_value**2), 4),
        "r": round(float(r_value), 4),
        "p_valor": round(float(p_value), 4),
        "error_estandar": round(float(std_err), 4),
        "significativo": p_value <= 0.05,
        "n": len(mask),
    }


def chi_cuadrado(df, var1, var2):
    """Test de chi-cuadrado de independencia."""
    tabla = pd.crosstab(df[var1], df[var2])
    chi2, p, dof, expected = stats.chi2_contingency(tabla)
    
    return {
        "test": "Chi-cuadrado de independencia",
        "chi2": round(float(chi2), 4),
        "p_valor": round(float(p), 4),
        "grados_libertad": int(dof),
        "significativo": p <= 0.05,
        "tabla": tabla.to_dict(),
    }


def kaplan_meier(df, var_tiempo, var_evento, var_grupo=None):
    """Curva de Kaplan-Meier."""
    from lifelines import KaplanMeierFitter
    
    if var_grupo:
        kmfs = {}
        for grupo in df[var_grupo].dropna().unique():
            mask = df[var_grupo] == grupo
            kmf = KaplanMeierFitter()
            kmf.fit(df.loc[mask, var_tiempo], event_observed=df.loc[mask, var_evento], label=str(grupo))
            kmfs[str(grupo)] = kmf
        return kmfs
    else:
        kmf = KaplanMeierFitter()
        kmf.fit(df[var_tiempo], event_observed=df[var_evento], label="Global")
        return {"Global": kmf}
