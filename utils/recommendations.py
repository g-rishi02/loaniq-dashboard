"""
LoanIQ — AI Recommendation Engine + Loan Health Score.

Rule-based prescriptive layer on top of model predictions.
Translates raw probabilities into actionable, human-readable guidance.
"""

from __future__ import annotations


def calculate_health_score(approval_prob: float, default_prob: float) -> float:
    """
    Composite Loan Health Score (0–100).

    Formula:  score = 0.6 × approval_prob + 0.4 × (1 − default_prob)
    Rationale:
      - Approval signal weighted 60% (primary gate)
      - Default safety weighted 40% (secondary risk check)
    """
    score = 0.6 * approval_prob + 0.4 * (1.0 - default_prob)
    return round(score * 100, 1)


def generate_recommendations(
    input_data: dict,
    approval_prob: float,
    default_prob: float,
) -> dict:
    """
    Generate prioritised, actionable recommendations.

    Returns:
        {
          "status": str,               # enum describing overall outcome
          "items":  list[dict],        # list of recommendation dicts
        }

    Each item:
        {
          "severity": "high" | "medium" | "ok",
          "title":    str,
          "detail":   str,
        }
    """
    items: list[dict] = []

    fico     = input_data.get("fico_avg",    700)
    dti      = input_data.get("dti",         25.0)
    loan     = input_data.get("loan_amnt",   15000)
    income   = input_data.get("annual_inc",  60000)
    emp      = input_data.get("emp_length",  "5 years")
    purpose  = input_data.get("purpose",     "other")

    lti = loan / max(income, 1)

    # ── FICO ──────────────────────────────────────────────────────────────
    if fico < 580:
        items.append({
            "severity": "high",
            "title":    f"Credit score too low ({fico})",
            "detail":   (
                f"A FICO score below 580 is considered Poor. Aim for at least 670 (Good) "
                f"before reapplying. Pay down revolving balances, correct any errors on your "
                f"credit report, and avoid new hard inquiries for 6–12 months."
            ),
        })
    elif fico < 670:
        items.append({
            "severity": "medium",
            "title":    f"Fair credit score ({fico}) — room to improve",
            "detail":   (
                f"Raising your FICO from {fico} to 670+ (Good) could meaningfully improve "
                f"approval odds and lower your interest rate. Focus on on-time payments and "
                f"reducing credit utilisation below 30%."
            ),
        })
    else:
        items.append({
            "severity": "ok",
            "title":    f"Strong credit score ({fico})",
            "detail":   "Your FICO score meets or exceeds the Good threshold. This is a positive signal.",
        })

    # ── DTI ───────────────────────────────────────────────────────────────
    if dti > 43:
        items.append({
            "severity": "high",
            "title":    f"Debt-to-income ratio very high ({dti:.1f}%)",
            "detail":   (
                f"A DTI above 43% signals excessive existing debt. Lenders typically require DTI "
                f"below 36% for prime rates. Consider paying off existing debts or increasing income "
                f"before applying. Target DTI: below 30%."
            ),
        })
    elif dti > 35:
        items.append({
            "severity": "medium",
            "title":    f"DTI elevated ({dti:.1f}%) — consider reducing",
            "detail":   (
                f"Your DTI of {dti:.1f}% is above the preferred 35% threshold. Reducing monthly debt "
                f"obligations by RM {_monthly_debt_reduction(dti, income, 30):,.0f} "
                f"would bring DTI to 30%."
            ),
        })
    else:
        items.append({
            "severity": "ok",
            "title":    f"Healthy DTI ratio ({dti:.1f}%)",
            "detail":   "Your debt-to-income ratio is within acceptable range.",
        })

    # ── Loan-to-income ─────────────────────────────────────────────────────
    if lti > 0.75:
        items.append({
            "severity": "high",
            "title":    f"Loan amount is large relative to income ({lti:.1f}x annual income)",
            "detail":   (
                f"Borrowing RM {loan:,} against an income of RM {income:,} creates a "
                f"{lti:.1f}x ratio. Consider reducing the loan to "
                f"RM {int(income * 0.5):,} (0.5× income) to improve approval odds."
            ),
        })
    elif lti > 0.40:
        items.append({
            "severity": "medium",
            "title":    f"Loan-to-income ratio moderate ({lti:.2f}x)",
            "detail":   (
                f"A smaller loan amount or income verification documentation could "
                f"strengthen this application."
            ),
        })
    else:
        items.append({
            "severity": "ok",
            "title":    f"Loan amount reasonable for income level",
            "detail":   f"RM {loan:,} represents {lti*100:.0f}% of annual income — within comfortable range.",
        })

    # ── Employment length ──────────────────────────────────────────────────
    emp_map = {"< 1 year":0,"1 year":1,"2 years":2,"3 years":3,"4 years":4,
               "5 years":5,"6 years":6,"7 years":7,"8 years":8,"9 years":9,"10+ years":10}
    emp_yrs = emp_map.get(emp, 5)
    if emp_yrs < 1:
        items.append({
            "severity": "medium",
            "title":    "Short employment history (< 1 year)",
            "detail":   (
                "Less than one year of employment is a minor negative signal. "
                "If recently employed in a higher-paying role, provide offer letter or payslips "
                "as supporting documentation."
            ),
        })

    # ── Default risk specific advice ───────────────────────────────────────
    if default_prob >= 0.50:
        items.append({
            "severity": "high",
            "title":    "High predicted default probability",
            "detail":   (
                f"The model estimates a {default_prob*100:.1f}% probability of default. "
                f"Consider a shorter loan term (36 months vs 60), a smaller loan amount, "
                f"or adding a co-borrower with a stronger credit profile."
            ),
        })
    elif default_prob >= 0.20:
        items.append({
            "severity": "medium",
            "title":    "Moderate default risk — manageable",
            "detail":   (
                f"Default probability is {default_prob*100:.1f}%. "
                f"Maintaining on-time payments and keeping credit utilisation low will "
                f"improve your risk profile over time."
            ),
        })

    # ── Determine overall status ───────────────────────────────────────────
    approved = approval_prob >= 0.50
    if approved and default_prob < 0.20:
        status = "approved_low_risk"
    elif approved and default_prob < 0.50:
        status = "approved_medium_risk"
    elif approved:
        status = "approved_high_risk"
    else:
        status = "rejected"

    # Sort: high → medium → ok
    severity_order = {"high": 0, "medium": 1, "ok": 2}
    items.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return {"status": status, "items": items}


def _monthly_debt_reduction(current_dti: float, annual_inc: float, target_dti: float) -> float:
    """Calculate monthly debt reduction needed to reach target DTI."""
    monthly_inc     = annual_inc / 12
    current_monthly = current_dti / 100 * monthly_inc
    target_monthly  = target_dti  / 100 * monthly_inc
    return max(0.0, current_monthly - target_monthly)
