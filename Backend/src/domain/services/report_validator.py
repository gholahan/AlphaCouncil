"""
Report Consistency Validator Service
Sprint 1 Specification -- MAD Finance
Validates financial reconciliation, verdict-to-action consistency, and report completeness.
"""

from typing import List
from src.domain.models.cio_report import CIOInvestmentReport


class ReportConsistencyValidator:
    """
    Validates financial reconciliation and verdict-action alignment across the CIO report.
    """

    @staticmethod
    def validate(report: CIOInvestmentReport) -> List[str]:
        errors = []
        rec = report.recommendation
        verdict = report.verdict

        # 1. Verdict to Action Consistency (§4.3)
        if verdict in ["Sell", "Strong Sell"]:
            if rec.proposed_allocation > 0 or rec.share_quantity > 0:
                errors.append(f"Verdict is '{verdict}', but recommendation proposes buying shares/allocating capital (> 0).")

        if verdict == "Hold":
            if rec.allocation_percentage > 10.0:
                errors.append(f"Verdict is 'Hold', but proposed allocation ({rec.allocation_percentage}%) exceeds recommended maximum retention threshold (10%).")

        # 2. Financial Reconciliation (§4.2)
        expected_remaining = rec.available_capital - rec.proposed_allocation - rec.transaction_costs
        if abs(expected_remaining - rec.remaining_cash) > 1.0:
            errors.append(
                f"Remaining cash reconciliation failed: available ({rec.available_capital}) - allocation ({rec.proposed_allocation}) - costs ({rec.transaction_costs}) = {expected_remaining}, but remaining_cash is {rec.remaining_cash}."
            )

        if rec.proposed_allocation > 0 and rec.entry_price and rec.entry_price > 0:
            expected_net_capital = rec.proposed_allocation - rec.transaction_costs
            expected_shares = int(expected_net_capital / rec.entry_price)
            if abs(expected_shares - rec.share_quantity) > 1:
                errors.append(
                    f"Share quantity mismatch: calculated {expected_shares} shares from net allocation, but recommendation states {rec.share_quantity} shares."
                )

        # 3. Completeness checks
        if not report.chat_response or len(report.chat_response.strip()) < 300:
            errors.append("Unified chat_response report is missing or too short.")

        return errors
