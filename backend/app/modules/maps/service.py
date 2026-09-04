from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import math
import uuid
import httpx

from ...db.models.patient import Patient
from ...db.models.hospital import Hospital
from ...db.models.alert import Alert
from ...core.config import settings

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
# Nominatim's usage policy requires a descriptive User-Agent identifying the app.
NOMINATIM_USER_AGENT = "SETU-Health-Platform/1.0 (post-discharge rural patient monitoring)"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometers."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float("inf")
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class MapsService:
    """Maps and location service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_asha_patients_location(self, asha_id: str) -> Dict[str, Any]:
        """Get patient locations for ASHA map"""
        # Get patients assigned to ASHA
        patients_stmt = select(Patient).filter(Patient.assigned_asha_id == uuid.UUID(asha_id))
        patients_result = await self.db.execute(patients_stmt)
        patients = patients_result.scalars().all()

        # Get critical patients
        critical_patients_stmt = (
            select(Patient)
            .filter(Patient.assigned_asha_id == uuid.UUID(asha_id))
            .filter(Patient.risk_level == "critical")
        )
        critical_result = await self.db.execute(critical_patients_stmt)
        critical_patients = critical_result.scalars().all()

        return {
            "patients": [
                {
                    "id": str(p.id),
                    "mrn": p.mrn,
                    "full_name": p.full_name,
                    "village": p.village,
                    "risk_level": p.risk_level,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                }
                for p in patients
            ],
            "critical_patients": [
                {
                    "id": str(p.id),
                    "mrn": p.mrn,
                    "full_name": p.full_name,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                }
                for p in critical_patients
            ],
            "center": {
                "lat": patients[0].latitude if patients else 12.9716,
                "lng": patients[0].longitude if patients else 77.5946,
            },
        }

    async def get_hospital_patients_location(self, hospital_id: str) -> Dict[str, Any]:
        """Get patient locations for hospital map"""
        patients_stmt = select(Patient).filter(Patient.hospital_id == uuid.UUID(hospital_id))
        patients_result = await self.db.execute(patients_stmt)
        patients = patients_result.scalars().all()

        hospital_stmt = select(Hospital).filter(Hospital.id == uuid.UUID(hospital_id))
        hospital_result = await self.db.execute(hospital_stmt)
        hospital = hospital_result.scalar_one_or_none()

        return {
            "hospital": {
                "id": str(hospital.id),
                "name": hospital.name,
                "latitude": hospital.latitude,
                "longitude": hospital.longitude,
            } if hospital else None,
            "patients": [
                {
                    "id": str(p.id),
                    "mrn": p.mrn,
                    "full_name": p.full_name,
                    "village": p.village,
                    "address": p.address,
                    "risk_level": p.risk_level,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                }
                for p in patients
            ],
            "center": {
                "lat": (hospital.latitude if hospital else None) or (patients[0].latitude if patients else 12.9716),
                "lng": (hospital.longitude if hospital else None) or (patients[0].longitude if patients else 77.5946),
            },
        }

    async def get_nearby_hospitals(self, patient_id: str, limit: int = 5) -> Dict[str, Any]:
        """Find hospitals nearest to a patient's stored location (plain
        Haversine distance over existing coordinates — no external API)."""
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()

        if not patient:
            return {"error": "Patient not found"}

        hospitals_stmt = select(Hospital).filter(Hospital.is_active == True)
        hospitals_result = await self.db.execute(hospitals_stmt)
        hospitals = hospitals_result.scalars().all()

        ranked = sorted(
            (
                {
                    "id": str(h.id),
                    "name": h.name,
                    "type": h.type,
                    "address": h.address,
                    "contact_phone": h.contact_phone,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "distance_km": round(haversine_km(patient.latitude, patient.longitude, h.latitude, h.longitude), 1),
                }
                for h in hospitals
            ),
            key=lambda h: h["distance_km"],
        )

        return {
            "patient": {
                "id": str(patient.id),
                "full_name": patient.full_name,
                "latitude": patient.latitude,
                "longitude": patient.longitude,
            },
            "hospitals": ranked[:limit],
        }

    async def geocode_address(self, query: str) -> Dict[str, Any]:
        """Look up coordinates for a free-text address via the public
        Nominatim API (OpenStreetMap). Light use only — respects the
        service's usage policy (identifying User-Agent, no bulk queries)."""
        if not query or not query.strip():
            return {"results": []}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{NOMINATIM_BASE_URL}/search",
                    params={"q": query, "format": "jsonv2", "limit": 5, "countrycodes": "in"},
                    headers={"User-Agent": NOMINATIM_USER_AGENT},
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            return {"results": [], "error": str(e)}

        return {
            "results": [
                {
                    "display_name": item.get("display_name"),
                    "latitude": float(item["lat"]),
                    "longitude": float(item["lon"]),
                }
                for item in data
            ]
        }

    async def get_emergency_response(
        self,
        patient_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Process emergency response request"""
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()

        if not patient:
            return {"error": "Patient not found"}

        return {
            "patient_id": patient_id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "latitude": patient.latitude,
            "longitude": patient.longitude,
            "address": patient.address,
            "nearest_hospital": patient.hospital_id,
            "response_dispatched": True,
        }

    async def generate_map_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate map data based on parameters"""
        map_type = params.get("type", "asha")
        user_id = params.get("user_id")

        if map_type == "asha":
            return await self.get_asha_patients_location(user_id)
        elif map_type == "hospital":
            return await self.get_hospital_patients_location(user_id)

        return {"patients": [], "center": {"lat": 0, "lng": 0}}
