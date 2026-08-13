"""Curated prenatal schedule and pregnancy date validation.

Content is limited to milestones supported by approved Singapore healthcare
sources. This module is an educational planning aid, not a medical care plan.
"""
from datetime import date
from typing import Optional


def validate_pregnancy_dates(
    conception_method: str,
    edd_date: date,
    fet_date: Optional[date] = None,
) -> list[str]:
    errors: list[str] = []
    if conception_method == "IVF":
        if fet_date is None:
            errors.append("Please enter the embryo transfer (FET) date.")
        elif edd_date <= fet_date:
            errors.append(
                "Invalid dates: Estimated Due Date (EDD) must be later than "
                "the embryo transfer (FET) date."
            )
    return errors


_SCHEDULE = [
    {
        "week_start": 6, "week_end": 12, "week_label": "Weeks 6-12",
        "title": "Dating scan and initial antenatal tests",
        "details": (
            "A dating ultrasound may be scheduled to confirm the pregnancy, "
            "estimate the due date and assess the pregnancy. Initial antenatal "
            "care commonly includes blood and urine tests. HealthHub describes "
            "full blood count and hepatitis B screening in this period."
        ),
        "optional": False,
        "source_name": "HealthHub - Tests for me and my baby",
        "source_url": "https://www.healthhub.sg/well-being-and-lifestyle/pregnancy-and-infant-health/pregnancy-tests-for-me-and-my-baby",
    },
    {
        "week_start": 11, "week_end": 14, "week_label": "Weeks 11-14",
        "title": "First-trimester / Down syndrome screening",
        "details": (
            "First-trimester screening may include an ultrasound and blood "
            "test. HealthHub describes nuchal translucency measurement and a "
            "combined test during weeks 11-14. KKH describes first-trimester "
            "screening as optional."
        ),
        "optional": True,
        "source_name": "SingHealth / KKH - Your Pregnancy Journey in KKH",
        "source_url": "https://www.singhealth.com.sg/tests-procedures/your-pregnancy-journey-in-kkh",
    },
    {
        "week_start": 15, "week_end": 20, "week_label": "Weeks 15-20",
        "title": "Additional prenatal screening where appropriate",
        "details": (
            "Depending on the screening pathway chosen with your healthcare "
            "professional, maternal serum screening may be performed during "
            "this period. Diagnostic tests such as amniocentesis are not "
            "routine for everyone and require individual clinical discussion."
        ),
        "optional": True,
        "source_name": "HealthHub - Tests for me and my baby",
        "source_url": "https://www.healthhub.sg/well-being-and-lifestyle/pregnancy-and-infant-health/pregnancy-tests-for-me-and-my-baby",
    },
    {
        "week_start": 18, "week_end": 22, "week_label": "Weeks 18-22",
        "title": "Detailed fetal anomaly ultrasound",
        "details": (
            "A detailed ultrasound / fetal anomaly scan is performed around "
            "this stage to assess fetal development and look for structural "
            "abnormalities. KKH describes a 20-week fetal anomaly scan."
        ),
        "optional": False,
        "source_name": "HealthHub - Tests for me and my baby",
        "source_url": "https://www.healthhub.sg/well-being-and-lifestyle/pregnancy-and-infant-health/pregnancy-tests-for-me-and-my-baby",
    },
    {
        "week_start": 24, "week_end": 28, "week_label": "Weeks 24-28",
        "title": "Gestational diabetes and anaemia screening",
        "details": (
            "Screening for gestational diabetes is usually performed at "
            "24-28 weeks. KKH also describes screening for anaemia during "
            "this period."
        ),
        "optional": False,
        "source_name": "NUH - Gestational Diabetes",
        "source_url": "https://www.nuh.com.sg/health-resources/diseases-and-conditions/gestational-diabetes",
    },
    {
        "week_start": 28, "week_end": 32, "week_label": "Weeks 28-32",
        "title": "Third-trimester growth assessment",
        "details": (
            "A growth scan may be offered in the third trimester to assess "
            "the baby's growth and wellbeing. KKH describes weeks 28-32, "
            "while NUH describes a growth scan at about 32 weeks."
        ),
        "optional": False,
        "source_name": "SingHealth / KKH - Your Pregnancy Journey in KKH",
        "source_url": "https://www.singhealth.com.sg/tests-procedures/your-pregnancy-journey-in-kkh",
    },
    {
        "week_start": 35, "week_end": 37, "week_label": "Weeks 35-37",
        "title": "Group B Streptococcus (GBS) screening",
        "details": (
            "KKH recommends a vaginal and rectal swab during weeks 35-37 to "
            "check for Group B Streptococcus (GBS)."
        ),
        "optional": False,
        "source_name": "SingHealth / KKH - Your Pregnancy Journey in KKH",
        "source_url": "https://www.singhealth.com.sg/tests-procedures/your-pregnancy-journey-in-kkh",
    },
]


def generate_prenatal_schedule(current_week: int, conception_method: str) -> list[dict]:
    if not 1 <= int(current_week) <= 42:
        raise ValueError("Current pregnancy week must be between 1 and 42.")
    return [dict(item) for item in _SCHEDULE]
