# colab_churn_card.py
from IPython.display import HTML, display
from html import escape
import json
import math
import uuid

import numpy as np
import pandas as pd


CSS_URL = "https://cdn.jsdelivr.net/gh/THEgoodbunny/coisa_sem_necessidade_de_existir@main/churn-card.css"
JS_URL = "https://cdn.jsdelivr.net/gh/THEgoodbunny/coisa_sem_necessidade_de_existir@main/churn-card.js"


def build_churn_payload(
    df,
    target_col="Churn",
    positive_labels=("yes", "sim", "true", "1"),
    title="Visão geral de clientes",
    eyebrow="Churn Analytics",
):
    work = df.copy()

    # -----------------------------
    # 1. Helpers gerais
    # -----------------------------
    def resolve_col(alias_list):
        for col in alias_list:
            if col in work.columns:
                return col

        lower_map = {str(c).lower().strip(): c for c in work.columns}

        for col in alias_list:
            key = str(col).lower().strip()
            if key in lower_map:
                return lower_map[key]

        return None

    colmap = {
        "tenure": resolve_col(["Retencao", "tenure", "Tenure"]),
        "monthly": resolve_col(["CobrancaMensal", "MonthlyCharges", "Monthly Charges"]),
        "total": resolve_col(["CobrancaTotal", "TotalCharges", "Total Charges"]),
        "senior": resolve_col(["ClienteSenior", "SeniorCitizen", "Senior Citizen"]),
        "contract": resolve_col(["Contrato", "Contract"]),
        "internet": resolve_col(["InternetService", "Internet Service", "ServicoInternet"]),
        "payment": resolve_col(["MetodoPagamento", "PaymentMethod", "Payment Method"]),
        "tech_support": resolve_col(["TechSupport", "Tech Support", "SuporteTecnico"]),
        "online_security": resolve_col(["OnlineSecurity", "Online Security", "SegurancaOnline"]),
    }

    def fmt_int(value):
        if pd.isna(value):
            return "n/d"
        return f"{int(round(value)):,}".replace(",", ".")

    def fmt_float(value, digits=1):
        if pd.isna(value):
            return "n/d"
        return f"{float(value):.{digits}f}".replace(".", ",")

    def fmt_pct(value):
        if pd.isna(value):
            return "n/d"
        return f"{float(value) * 100:.1f}%".replace(".", ",")

    def fmt_money(value):
        if pd.isna(value):
            return "n/d"
        s = f"R$ {float(value):,.2f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    def normalize_series(s):
        return s.astype(str).str.strip().str.lower()

    def safe_numeric(col):
        if col is None:
            return

        work[col] = work[col].replace(r"^\s*$", np.nan, regex=True)
        work[col] = pd.to_numeric(work[col], errors="coerce")

    for key in ["tenure", "monthly", "total", "senior"]:
        safe_numeric(colmap[key])

    # -----------------------------
    # 2. Máscaras de Churn
    # -----------------------------
    if target_col not in work.columns:
        raise ValueError(
            f"Coluna alvo '{target_col}' não encontrada. "
            f"Colunas disponíveis: {list(work.columns)}"
        )

    raw_target = work[target_col]
    valid_mask = raw_target.notna() & raw_target.astype(str).str.strip().ne("")

    work[target_col] = raw_target.astype(str).str.strip()
    target_norm = normalize_series(work[target_col])

    positive_set = {str(x).lower().strip() for x in positive_labels}
    yes_mask = target_norm.isin(positive_set)

    base_data = work.loc[valid_mask]
    churn_data = work.loc[valid_mask & yes_mask]
    retained_data = work.loc[valid_mask & ~yes_mask]

    total = int(len(base_data))
    churn_yes = int(len(churn_data))
    retained = int(len(retained_data))

    churn_rate = churn_yes / total if total else 0
    retention_rate = retained / total if total else 0

    # -----------------------------
    # 3. Estatísticas por classe
    # -----------------------------
    def avg(data, col):
        if col is None or len(data) == 0:
            return np.nan
        return data[col].mean()

    def median(data, col):
        if col is None or len(data) == 0:
            return np.nan
        return data[col].median()

    def pct_truthy(data, col):
        if col is None or len(data) == 0:
            return np.nan

        s = data[col]

        if pd.api.types.is_numeric_dtype(s):
            return s.eq(1).mean()

        return normalize_series(s).isin(["yes", "sim", "true", "1"]).mean()

    def pct_in(data, col, expected_values):
        if col is None or len(data) == 0:
            return np.nan

        expected = {x.lower().strip() for x in expected_values}
        return normalize_series(data[col]).isin(expected).mean()

    def top_value(data, col):
        if col is None or len(data) == 0:
            return None, np.nan

        s = data[col].dropna().astype(str).str.strip()
        s = s[s.ne("")]

        if len(s) == 0:
            return None, np.nan

        vc = s.value_counts()
        label = vc.index[0]
        share = vc.iloc[0] / len(s)

        return label, share

    def collect_stats(data):
        contract_top, contract_share = top_value(data, colmap["contract"])
        internet_top, internet_share = top_value(data, colmap["internet"])
        payment_top, payment_share = top_value(data, colmap["payment"])

        return {
            "tenure_avg": avg(data, colmap["tenure"]),
            "tenure_median": median(data, colmap["tenure"]),
            "monthly_avg": avg(data, colmap["monthly"]),
            "monthly_median": median(data, colmap["monthly"]),
            "total_avg": avg(data, colmap["total"]),

            "senior_pct": pct_truthy(data, colmap["senior"]),
            "month_contract_pct": pct_in(data, colmap["contract"], ["month-to-month", "mensal"]),
            "fiber_pct": pct_in(data, colmap["internet"], ["fiber optic", "fibra óptica", "fibra optica"]),
            "electronic_check_pct": pct_in(data, colmap["payment"], ["electronic check", "cheque eletrônico", "cheque eletronico"]),
            "no_support_pct": pct_in(data, colmap["tech_support"], ["no", "não", "nao"]),
            "no_security_pct": pct_in(data, colmap["online_security"], ["no", "não", "nao"]),

            "contract_top": contract_top,
            "contract_share": contract_share,
            "internet_top": internet_top,
            "internet_share": internet_share,
            "payment_top": payment_top,
            "payment_share": payment_share,
        }

    base_stats = collect_stats(base_data)
    churn_stats = collect_stats(churn_data)
    retained_stats = collect_stats(retained_data)

    # -----------------------------
    # 4. Tooltip HTML
    # -----------------------------
    def delta_class(diff):
        if pd.isna(diff) or abs(diff) < 1e-12:
            return "neutral"
        return "up" if diff > 0 else "down"

    def delta_num(current, base, suffix="", digits=1):
        if pd.isna(current) or pd.isna(base):
            return ""

        diff = current - base
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        sign = "+" if diff > 0 else ""
        text = f"{arrow} {sign}{fmt_float(diff, digits)}{suffix} vs base"

        return f"<span class='ca-delta ca-{delta_class(diff)}'>{escape(text)}</span>"

    def delta_money(current, base):
        if pd.isna(current) or pd.isna(base):
            return ""

        diff = current - base
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        sign = "+" if diff > 0 else "-"
        text = f"{arrow} {sign}{fmt_money(abs(diff))} vs base"

        return f"<span class='ca-delta ca-{delta_class(diff)}'>{escape(text)}</span>"

    def delta_pp(current, base):
        if pd.isna(current) or pd.isna(base):
            return ""

        diff = (current - base) * 100
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        sign = "+" if diff > 0 else ""
        text = f"{arrow} {sign}{fmt_float(diff, 1)} p.p. vs base"

        return f"<span class='ca-delta ca-{delta_class(diff)}'>{escape(text)}</span>"

    def row(label, value, delta=""):
        return f"""
            <div class="ca-tooltip-row">
                <span>{escape(str(label))}</span>
                <b>{escape(str(value))}</b>
                {delta}
            </div>
        """

    def top_row(label, top, share):
        if top is None or pd.isna(share):
            return ""

        return row(
            label,
            top,
            f"<span class='ca-delta ca-neutral'>{escape(fmt_pct(share))} da classe</span>",
        )

    def divider():
        return '<div class="ca-tooltip-divider"></div>'

    def tooltip_block(class_name, label, count, share, stats, note):
        rows = [
            row(
                "Clientes",
                fmt_int(count),
                f"<span class='ca-delta ca-neutral'>{escape(fmt_pct(share))} da base</span>",
            ),
            row(
                "Retenção média",
                f"{fmt_float(stats['tenure_avg'])} meses",
                delta_num(stats["tenure_avg"], base_stats["tenure_avg"], " meses"),
            ),
            row(
                "Retenção mediana",
                f"{fmt_float(stats['tenure_median'])} meses",
                delta_num(stats["tenure_median"], base_stats["tenure_median"], " meses"),
            ),
            row(
                "Cobrança mensal média",
                fmt_money(stats["monthly_avg"]),
                delta_money(stats["monthly_avg"], base_stats["monthly_avg"]),
            ),
            row(
                "Cobrança mensal mediana",
                fmt_money(stats["monthly_median"]),
                delta_money(stats["monthly_median"], base_stats["monthly_median"]),
            ),
            row(
                "Cobrança total média",
                fmt_money(stats["total_avg"]),
                delta_money(stats["total_avg"], base_stats["total_avg"]),
            ),
            divider(),
            top_row("Contrato dominante", stats["contract_top"], stats["contract_share"]),
            top_row("Internet dominante", stats["internet_top"], stats["internet_share"]),
            top_row("Pagamento dominante", stats["payment_top"], stats["payment_share"]),
            divider(),
            row(
                "Cliente sênior",
                fmt_pct(stats["senior_pct"]),
                delta_pp(stats["senior_pct"], base_stats["senior_pct"]),
            ),
            row(
                "Contrato mensal",
                fmt_pct(stats["month_contract_pct"]),
                delta_pp(stats["month_contract_pct"], base_stats["month_contract_pct"]),
            ),
            row(
                "Fibra óptica",
                fmt_pct(stats["fiber_pct"]),
                delta_pp(stats["fiber_pct"], base_stats["fiber_pct"]),
            ),
            row(
                "Electronic check",
                fmt_pct(stats["electronic_check_pct"]),
                delta_pp(stats["electronic_check_pct"], base_stats["electronic_check_pct"]),
            ),
            row(
                "Sem suporte técnico",
                fmt_pct(stats["no_support_pct"]),
                delta_pp(stats["no_support_pct"], base_stats["no_support_pct"]),
            ),
            row(
                "Sem segurança online",
                fmt_pct(stats["no_security_pct"]),
                delta_pp(stats["no_security_pct"], base_stats["no_security_pct"]),
            ),
        ]

        return f"""
            <div class="ca-tooltip-title">
                <span class="ca-dot ca-dot-{escape(class_name)}"></span>
                {escape(label)}
            </div>

            {''.join(rows)}

            <div class="ca-tooltip-note">{escape(note)}</div>
        """

    def top_row_overall(label, top, share):
        if top is None or pd.isna(share):
            return ""

        return row(
            label,
            top,
            f"<span class='ca-delta ca-neutral'>{escape(fmt_pct(share))} da base</span>",
        )

    def tooltip_overall_block():
        rows = [
            row(
                "Linhas no DF",
                fmt_int(len(work)),
                "<span class='ca-delta ca-neutral'>total carregado</span>",
            ),
            row(
                "Clientes válidos",
                fmt_int(total),
                "<span class='ca-delta ca-neutral'>com Churn preenchido</span>",
            ),
            row(
                "Churn",
                fmt_int(churn_yes),
                f"<span class='ca-delta ca-neutral'>{escape(fmt_pct(churn_rate))} da base</span>",
            ),
            row(
                "Retidos",
                fmt_int(retained),
                f"<span class='ca-delta ca-neutral'>{escape(fmt_pct(retention_rate))} da base</span>",
            ),
            divider(),
            row("Retenção média", f"{fmt_float(base_stats['tenure_avg'])} meses"),
            row("Retenção mediana", f"{fmt_float(base_stats['tenure_median'])} meses"),
            row("Cobrança mensal média", fmt_money(base_stats["monthly_avg"])),
            row("Cobrança mensal mediana", fmt_money(base_stats["monthly_median"])),
            row("Cobrança total média", fmt_money(base_stats["total_avg"])),
            divider(),
            top_row_overall("Contrato dominante", base_stats["contract_top"], base_stats["contract_share"]),
            top_row_overall("Internet dominante", base_stats["internet_top"], base_stats["internet_share"]),
            top_row_overall("Pagamento dominante", base_stats["payment_top"], base_stats["payment_share"]),
            divider(),
            row("Cliente sênior", fmt_pct(base_stats["senior_pct"])),
            row("Contrato mensal", fmt_pct(base_stats["month_contract_pct"])),
            row("Fibra óptica", fmt_pct(base_stats["fiber_pct"])),
            row("Electronic check", fmt_pct(base_stats["electronic_check_pct"])),
            row("Sem suporte técnico", fmt_pct(base_stats["no_support_pct"])),
            row("Sem segurança online", fmt_pct(base_stats["no_security_pct"])),
        ]

        return f"""
            <div class="ca-tooltip-title">
                <span class="ca-dot ca-dot-overall"></span>
                Perfil estatístico: Base geral
            </div>

            {''.join(rows)}

            <div class="ca-tooltip-note">Leitura: resumo estatístico da base inteira usada no card. Linhas com Churn vazio não entram nas proporções de churn/retidos.</div>
        """

    tooltip_content = {
        "overall": tooltip_overall_block(),
        "retained": tooltip_block(
            "retained",
            "Perfil estatístico: Retidos",
            retained,
            retention_rate,
            retained_stats,
            "Leitura: valores comparados contra a base inteira. Delta positivo nem sempre é ruim; depende da métrica.",
        ),
        "churn": tooltip_block(
            "churn",
            "Perfil estatístico: Churn",
            churn_yes,
            churn_rate,
            churn_stats,
            "Leitura: concentração acima da base indica possível associação com churn, não causalidade isolada.",
        ),
    }

    return {
        "title": title,
        "eyebrow": eyebrow,
        "total": total,
        "churn_yes": churn_yes,
        "retained": retained,
        "churn_rate": churn_rate,
        "retention_rate": retention_rate,
        "total_label": fmt_int(total),
        "churn_label": fmt_int(churn_yes),
        "retained_label": fmt_int(retained),
        "churn_rate_label": fmt_pct(churn_rate),
        "retention_rate_label": fmt_pct(retention_rate),
        "badge_label": "Base geral",
        "tooltip": tooltip_content,
    }


def render_churn_card(payload, css_url=CSS_URL, js_url=JS_URL):
    uid = f"churn_{uuid.uuid4().hex[:8]}"
    payload_json = json.dumps(payload, ensure_ascii=False)

    html = f"""
    <link rel="stylesheet" href="{css_url}">

    <div id="{uid}"></div>

    <script>
        (() => {{
            const payload = {payload_json};
            const selector = "#{uid}";

            const doRender = () => {{
                if (!window.ChurnCard || !window.ChurnCard.render) return;
                window.ChurnCard.render(selector, payload);
            }};

            if (window.ChurnCard && window.ChurnCard.render) {{
                doRender();
                return;
            }}

            const existingScript = document.querySelector('script[data-churn-card-js="true"]');

            if (existingScript) {{
                existingScript.addEventListener("load", doRender, {{ once: true }});
                return;
            }}

            const script = document.createElement("script");
            script.src = "{js_url}";
            script.dataset.churnCardJs = "true";
            script.onload = doRender;
            document.body.appendChild(script);
        }})();
    </script>
    """

    display(HTML(html))


# Exemplo de uso no Colab:
#
# import pandas as pd
# df = pd.read_csv("/content/churnCLARO(1).csv")
#
# payload = build_churn_payload(df)
# render_churn_card(payload)
