from app.tasks.celery_app import celery_app
from app.services.report_generator import generate_imo_dcs_report


@celery_app.task(bind=True, name="generate_report")
def generate_report_task(
    self,
    org_id: str,
    org_name: str,
    year: int,
    ships: list[dict],
    emissions_records: list[dict],
    voyages: list[dict],
) -> str:
    """Celery task to generate an IMO DCS Annual Compliance Report PDF."""
    pdf_path = generate_imo_dcs_report(
        org_id=org_id,
        org_name=org_name,
        year=year,
        ships=ships,
        emissions_records=emissions_records,
        voyages=voyages,
    )
    return pdf_path
