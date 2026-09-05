import asyncio
import base64
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import os
import httpx

from ...core.database import get_db, async_session
from ...core.config import settings
from .service import CallService
from ...modules.ivr.service import IVRService
from ...modules.speech.service import SpeechService
from ...db.models.call import Call
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User

logger = logging.getLogger("setu.calls.webhook")

router = APIRouter(prefix="/api/v1/calls", tags=["calls"])


@router.post("/outbound", response_model=dict)
async def create_outbound_call(
    patient_id: str,
    ivr_flow_id: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create outbound call to patient"""
    await authorize_patient_access(patient_id, user, db)
    service = CallService(db)
    return await service.create_outbound_call(patient_id, ivr_flow_id=ivr_flow_id)


class ScheduleCallRequest(BaseModel):
    patient_id: str
    scheduled_at: datetime
    repeat_daily: bool = False


@router.post("/schedule", response_model=dict)
async def schedule_call(
    request: ScheduleCallRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Schedule a future outbound check-in call for a minute-precise time —
    patient, ASHA, or hospital staff can all schedule one for a patient
    they're authorized to see. Reuses the Reminder table + the same
    background scheduler as medication reminders (core/scheduler.py):
    notification_method="call" tells send_reminder() to place a real call
    instead of sending a notification when it comes due, rather than
    building a second, parallel scheduling system."""
    await authorize_patient_access(request.patient_id, user, db)

    # scheduled_at arrives as a UTC-aware ISO string (frontend converts the
    # user's local wall-clock pick via Date.toISOString()) — strip tzinfo to
    # match this column's naive-UTC convention (same as datetime.utcnow()
    # everywhere else in this codebase); storing it tz-aware here would
    # silently break the scheduler's naive `<= datetime.utcnow()` comparison.
    scheduled_at = request.scheduled_at
    if scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)

    from ...db.models.reminder import Reminder
    reminder = Reminder(
        id=uuid.uuid4(),
        patient_id=uuid.UUID(request.patient_id),
        reminder_type="checkin_call",
        title="Scheduled Check-in Call",
        description="Automated SETU health check-in call",
        schedule_type="daily" if request.repeat_daily else "one_time",
        scheduled_at=scheduled_at,
        status="scheduled",
        notification_method="call",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(reminder)
    await db.commit()
    return {
        "id": str(reminder.id),
        "scheduled_at": reminder.scheduled_at.isoformat(),
        "repeat_daily": request.repeat_daily,
    }


@router.get("/{call_id}")
async def get_call(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get call by ID"""
    call_stmt = select(Call).filter(Call.id == uuid.UUID(call_id))
    result = await db.execute(call_stmt)
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    await authorize_patient_access(str(call.patient_id), user, db)
    return {"id": str(call.id), "status": call.status}


@router.get("/patient/{patient_id}/calls", response_model=list[dict])
async def get_patient_calls(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get calls for patient"""
    await authorize_patient_access(patient_id, user, db)
    service = CallService(db)
    return await service.get_patient_calls(patient_id)


@router.post("/webhook/status")
async def handle_call_status(
    call_id: str,
    status: str,
    recording_url: str = None,
    transcript: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle call status webhook"""
    service = CallService(db)
    return await service.handle_call_status(call_id, status, recording_url, transcript)


async def _find_active_call(
    db: AsyncSession,
    call_id: str = None,
    provider_call_id: str = None,
    to_number: str = None,
) -> Call | None:
    """Resolve the SETU Call record a Telnyx/Twilio voice webhook refers to.

    Telnyx/Twilio webhooks aren't authenticated with our JWTs, so a call is
    identified by whichever of these we have: our own call_id passed through
    the action URL's query string (most reliable — set once we know it),
    their CallSid (matches the provider_call_id we stored when the outbound
    call was placed), or as a last resort the most recent call to that phone
    number.
    """
    if call_id:
        try:
            stmt = select(Call).filter(Call.id == uuid.UUID(call_id))
            result = await db.execute(stmt)
            call = result.scalar_one_or_none()
            if call:
                return call
        except ValueError:
            pass
    if provider_call_id:
        stmt = select(Call).filter(Call.provider_call_id == provider_call_id)
        result = await db.execute(stmt)
        call = result.scalar_one_or_none()
        if call:
            return call
    if to_number:
        stmt = (
            select(Call)
            .filter(Call.to_number == to_number)
            .order_by(Call.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    return None


def _xml(voice_response) -> Response:
    return Response(content=str(voice_response), media_type="application/xml")


def _base_url() -> str:
    return settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""


@router.post("/webhook/twiml")
async def handle_call_twiml(
    CallSid: str = Form(None),
    From: str = Form(None),
    To: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Voice URL for the outbound check-in call — Telnyx's TeXML Application
    (or Twilio, when PUBLIC_BASE_URL is set) hits this the instant the call
    connects and expects TwiML/TeXML back describing what to say/do next.
    TeXML is a Twilio-compatible XML dialect, so the same tags work for both
    providers; NOTE this has been built against documented parameter names
    but not yet verified against a real Telnyx call — confirm the flow with
    one live test call once TELNYX_* credentials are configured.
    """
    from twilio.twiml.voice_response import VoiceResponse, Gather

    call = await _find_active_call(db, provider_call_id=CallSid, to_number=To)
    call_id = str(call.id) if call else ""
    base = _base_url()

    vr = VoiceResponse()
    vr.say(
        "Hello, this is SETU calling for your daily health check-in. "
        "This call may be recorded for your care team."
    )
    gather = Gather(
        num_digits=1,
        timeout=8,
        action=f"{base}/api/v1/calls/webhook/twiml/menu?call_id={call_id}",
        method="POST",
    )
    gather.say(
        "Press 1 if you are feeling fine today. "
        "Press 2 to report symptoms. "
        "Press 3 if this is an emergency."
    )
    vr.append(gather)

    # No digit pressed within the Gather's timeout: fall through to a voice
    # recording as a fallback so the check-in still completes.
    vr.say("We didn't get a response. Please describe how you're feeling after the tone.")
    vr.record(
        # Kept under Sarvam's 30s hard sync-API limit — see _record_fallback's
        # comment on the Call Control path for the confirmed-live failure mode.
        max_length=25,
        play_beep=True,
        action=f"{base}/api/v1/calls/webhook/twiml/voice?call_id={call_id}",
        method="POST",
    )
    vr.say("Thank you. Your care team will follow up if needed. Goodbye.")
    return _xml(vr)


@router.post("/webhook/twiml/menu")
async def handle_call_menu(
    call_id: str = None,
    Digits: str = Form(None),
    CallSid: str = Form(None),
    To: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handles the keypad digit pressed in response to /webhook/twiml's
    Gather. Feeds the result through the SAME deterministic clinical
    pipeline the patient app's check-in and ASHA/hospital chat use — the
    call is just another input channel, not a separate risk implementation.
    """
    from twilio.twiml.voice_response import VoiceResponse
    from ..clinical.service import ClinicalPipelineService

    call = await _find_active_call(db, call_id=call_id, provider_call_id=CallSid, to_number=To)
    vr = VoiceResponse()

    if not call:
        vr.say("Sorry, we could not find your check-in record. Your care team will follow up. Goodbye.")
        vr.hangup()
        return _xml(vr)

    clinical_service = ClinicalPipelineService(db)
    base = _base_url()

    if Digits == "1":
        await clinical_service.process_clinical_input(
            patient_id=str(call.patient_id),
            reporter="patient",
            input_text="Feeling fine, no symptoms reported.",
            explicit_symptoms=[],
            method="phone",
        )
        vr.say("Glad to hear it. Take care, and thank you for checking in. Goodbye.")
        vr.hangup()

    elif Digits == "2":
        vr.say("Please describe your symptoms after the tone, then press the pound key.")
        vr.record(
            max_length=60,
            play_beep=True,
            finish_on_key="#",
            action=f"{base}/api/v1/calls/webhook/twiml/voice?call_id={call_id}",
            method="POST",
        )
        vr.say("Thank you. Goodbye.")

    elif Digits == "3":
        # "IF emergency keypress: CRITICAL" — the deterministic rule engine's
        # first and highest-priority rule. severe_trauma is a critical-weight
        # symptom key (risk/rules.py) so this floors risk to CRITICAL exactly
        # like a real critical symptom report would.
        await clinical_service.process_clinical_input(
            patient_id=str(call.patient_id),
            reporter="patient",
            input_text="Emergency reported via phone keypad.",
            explicit_symptoms=["severe_trauma"],
            method="phone",
        )
        vr.say(
            "This has been marked as an emergency. Your ASHA worker and hospital "
            "are being alerted right now. Please stay calm."
        )
        vr.hangup()

    else:
        vr.say("Sorry, that wasn't a valid option. Your care team will follow up. Goodbye.")
        vr.hangup()

    call.status = "in_progress"
    call.dtmf_input = Digits
    await db.commit()
    return _xml(vr)


@router.post("/webhook/twiml/voice")
async def handle_call_voice(
    call_id: str = None,
    RecordingUrl: str = Form(None),
    RecordingDuration: str = Form(None),
    CallSid: str = Form(None),
    To: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handles a completed voice recording from either /webhook/twiml's or
    /webhook/twiml/menu's <Record> fallback: downloads the audio, transcribes
    it via the configured SpeechProvider, and feeds the transcript through
    the same deterministic clinical pipeline as every other input channel.

    NOTE: SPEECH_PROVIDER=sarvam is currently a stub (returns a fixed canned
    transcript, no real API call — see speech/providers/sarvam.py) — this
    path is wired correctly end-to-end, but the transcribed *content* won't
    reflect what the patient actually said until that provider is finished.
    The DTMF path (Digits 1/2/3) is unaffected and fully real.
    """
    from twilio.twiml.voice_response import VoiceResponse
    from ..clinical.service import ClinicalPipelineService

    call = await _find_active_call(db, call_id=call_id, provider_call_id=CallSid, to_number=To)
    vr = VoiceResponse()

    if not call or not RecordingUrl:
        vr.say("Sorry, we couldn't process your recording. Your care team will follow up. Goodbye.")
        vr.hangup()
        if call:
            call.status = "completed"
            await db.commit()
        return _xml(vr)

    transcript = ""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            audio_url = RecordingUrl if RecordingUrl.endswith((".wav", ".mp3")) else f"{RecordingUrl}.wav"
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()
            audio_bytes = audio_resp.content

        speech_service = SpeechService(db)
        transcription = await speech_service.transcribe_audio(audio_bytes)
        transcript = transcription.get("transcript", "") or ""
    except Exception as e:
        logger.error(f"Failed to fetch/transcribe recording for call {call.id}: {e}")

    clinical_service = ClinicalPipelineService(db)
    result = await clinical_service.process_clinical_input(
        patient_id=str(call.patient_id),
        reporter="patient",
        input_text=transcript or "No speech detected during check-in call.",
        method="phone",
    )

    call.status = "completed"
    call.recording_url = RecordingUrl
    call.speech_transcript = transcript
    await db.commit()

    risk_level = (result or {}).get("risk_level")
    if risk_level == "critical":
        vr.say(
            "Based on what you told us, this has been marked urgent. "
            "Your ASHA worker and hospital are being alerted right now."
        )
    else:
        vr.say("Thank you. Your care team has this information and will follow up if needed. Goodbye.")
    vr.hangup()
    return _xml(vr)


@router.post("/webhook/recording-status")
async def handle_recording_status(
    CallSid: str = Form(None),
    RecordingUrl: str = Form(None),
    RecordingDuration: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Defensive-net recordingStatusCallback: some Telnyx TeXML deployments
    deliver the recording only here (after the call ends), not via the
    <Record> action URL's callback. Persists it either way so it's never
    silently lost even if /webhook/twiml/voice's own capture is a miss."""
    if not CallSid or not RecordingUrl:
        return {"received": True}

    call = await _find_active_call(db, provider_call_id=CallSid)
    if call and not call.recording_url:
        call.recording_url = RecordingUrl
        await db.commit()
    return {"received": True}


_HANGUP_AFTER_SPEAK = base64.b64encode(b"hangup_after").decode()


async def _cc_action(call_control_id: str, name: str, body: dict) -> None:
    """Fire a Telnyx Call Control action (speak/gather/record/hangup). Fire-
    and-forget from the webhook handler's perspective — Telnyx reports the
    outcome via further webhook events, not this response."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/{name}",
                headers={
                    "Authorization": f"Bearer {settings.TELNYX_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            if resp.status_code >= 400:
                logger.error(f"Telnyx action '{name}' failed for {call_control_id}: {resp.text}")
    except Exception as e:
        logger.error(f"Telnyx action '{name}' failed for {call_control_id}: {e}")


async def _speak_then_hangup(call_control_id: str, text: str) -> None:
    """Speak a closing message and hang up once it finishes playing (not
    immediately — an immediate hangup can cut speech off mid-sentence,
    since these are independent async REST calls with no ordering
    guarantee). client_state round-trips on the call.speak.ended event
    that follows, which is what actually triggers the hangup."""
    await _cc_action(call_control_id, "speak", {
        "payload": text,
        "voice": "female",
        "language": "en-US",
        "client_state": _HANGUP_AFTER_SPEAK,
    })


async def _record_fallback(call_control_id: str) -> None:
    await _cc_action(call_control_id, "record_start", {
        "format": "mp3",
        "channels": "single",
        "play_beep": True,
        # Sarvam's synchronous speech-to-text REST API hard-rejects audio
        # over 30s ("use the batch API for longer files" — not built here).
        # Confirmed live: a recording that ran past 30s failed transcription
        # entirely, silently falling back to "no speech detected". Capped
        # comfortably under that ceiling rather than exactly at it.
        "max_length": 25,
        # Silence-detection cutoff — how long Telnyx keeps recording after
        # the patient stops talking before deciding they're done. Confirmed
        # live at 10s that this reads as a long awkward pause on the call;
        # lowered to a snappier gap while still tolerant of a brief pause
        # mid-sentence.
        "timeout_secs": 3,
    })


async def _process_gather_ended(call_id: uuid.UUID, call_control_id: str, digits: str) -> None:
    """The slow half of call.gather.ended for digits "1"/"3" (both call
    Gemini via process_clinical_input before responding) — see
    _process_recording_saved's docstring for why this runs as a background
    task with its own db session instead of inline in the webhook handler."""
    async with async_session() as db:
        call_stmt = select(Call).filter(Call.id == call_id)
        call_result = await db.execute(call_stmt)
        call = call_result.scalar_one_or_none()
        if not call:
            return

        from ..clinical.service import ClinicalPipelineService
        clinical_service = ClinicalPipelineService(db)

        if digits == "1":
            await clinical_service.process_clinical_input(
                patient_id=str(call.patient_id),
                reporter="patient",
                input_text="Feeling fine, no symptoms reported.",
                explicit_symptoms=[],
                method="phone",
            )
            await _speak_then_hangup(call_control_id, "Glad to hear it. Take care, and thank you for checking in. Goodbye.")

        elif digits == "2":
            await _cc_action(call_control_id, "speak", {
                "payload": "Please describe your symptoms after the tone.",
                "voice": "female",
                "language": "en-US",
            })
            await _record_fallback(call_control_id)

        elif digits == "3":
            # "IF emergency keypress: CRITICAL" — same deterministic rule as
            # the TeXML path above; severe_trauma floors risk to CRITICAL.
            await clinical_service.process_clinical_input(
                patient_id=str(call.patient_id),
                reporter="patient",
                input_text="Emergency reported via phone keypad.",
                explicit_symptoms=["severe_trauma"],
                method="phone",
            )
            await _speak_then_hangup(
                call_control_id,
                "This has been marked as an emergency. Your ASHA worker and hospital "
                "are being alerted right now. Please stay calm.",
            )

        else:
            # No digit pressed within the timeout: fall through to a voice
            # recording, same fallback as the TeXML path.
            await _cc_action(call_control_id, "speak", {
                "payload": "We didn't get a response. Please describe how you're feeling after the tone.",
                "voice": "female",
                "language": "en-US",
            })
            await _record_fallback(call_control_id)


async def _process_recording_saved(call_id: uuid.UUID, call_control_id: str, recording_url: str) -> None:
    """The slow half of call.recording.saved (audio fetch, transcription,
    clinical pipeline, AI guidance, speak+hangup) — runs as a background
    task with its OWN db session, independent of the webhook request's
    session, which the request handler already returned a response on and
    whose session may since have closed."""
    transcript = ""
    # Distinguish "the patient genuinely said nothing" from "we could not
    # hear them" — they must NOT be treated the same. Sarvam's sync STT is
    # measurably flaky (confirmed live: a real patient's spoken symptoms were
    # lost to a 30s read timeout), and feeding that into the clinical
    # pipeline as "no speech detected" quietly produces a NORMAL risk record
    # for a patient who may have just described an emergency.
    transcription_failed = False
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            audio_resp = await client.get(recording_url)
            audio_resp.raise_for_status()
            audio_bytes = audio_resp.content
        async with async_session() as db:
            speech_service = SpeechService(db)
            transcription = await speech_service.transcribe_audio(audio_bytes)
            transcript = transcription.get("transcript", "") or ""
            if transcription.get("error"):
                transcription_failed = True
                logger.error(
                    f"Transcription failed for call {call_id}: {transcription.get('error')}"
                )
    except Exception as e:
        transcription_failed = True
        logger.error(f"Failed to fetch/transcribe recording for call {call_id}: {e}")

    async with async_session() as db:
        call_stmt = select(Call).filter(Call.id == call_id)
        call_result = await db.execute(call_stmt)
        call = call_result.scalar_one_or_none()
        if not call:
            return

        result = None
        if transcription_failed:
            # We have audio the patient recorded but no idea what's in it.
            # Escalate to a human rather than writing a risk record off
            # speech we never actually read: the recording URL is on the
            # Call row, so the ASHA can listen to it and follow up.
            from ..alerts.service import AlertService
            alert_service = AlertService(db)
            await alert_service.create_alert(
                patient_id=str(call.patient_id),
                severity="high",
                title="Check-in call needs manual follow-up",
                description=(
                    "The patient answered the check-in call and recorded a response, but "
                    "automatic transcription failed, so their symptoms could not be read. "
                    "Listen to the recording or call the patient back."
                ),
                risk_level="warning",
                alert_type="system_alert",
                triggered_by="call_transcription_failure",
                metadata={"call_id": str(call.id), "recording_url": recording_url},
            )
            call.status = "needs_review"
        else:
            from ..clinical.service import ClinicalPipelineService
            clinical_service = ClinicalPipelineService(db)
            result = await clinical_service.process_clinical_input(
                patient_id=str(call.patient_id),
                reporter="patient",
                input_text=transcript or "No speech detected during check-in call.",
                method="phone",
            )

        call.speech_transcript = transcript
        await db.commit()

    if transcription_failed:
        # Tell the patient the truth: we couldn't hear them, and a human
        # will follow up — never a reassuring "thanks, all noted".
        await _speak_then_hangup(
            call_control_id,
            "Sorry, we could not hear your answer clearly. Your health worker has been "
            "notified and will call you back. If you feel unwell, please contact them or "
            "your nearest health centre right away.",
        )
        return

    risk_level = (result or {}).get("risk_level") or "normal"
    # AI phrases the SPOKEN advice for every risk level, including 'normal' —
    # the deterministic engine only recognizes a small fixed vocabulary
    # (chest pain, bleeding, fever, ...), so plenty of real complaints (a
    # fall, a cut, suspected food poisoning) correctly stay 'normal' but
    # still deserve real generic first-aid advice instead of a bare "thank
    # you". Gemini does NOT re-decide risk_level here — that's already
    # settled above — it only phrases what to say, same "AI extracts/
    # phrases, rules decide" pattern as chat's generate_response(). Falls
    # back to a safe generic message per tier if Gemini is unavailable or
    # the transcript was empty (nothing to tailor advice to).
    from ..chat.providers.gemini import GeminiChatProvider
    guidance = None
    gemini_provider = GeminiChatProvider()
    if gemini_provider.available() and transcript:
        try:
            guidance = await gemini_provider.generate_call_guidance(transcript, risk_level)
        except Exception as e:
            logger.error(f"Call guidance generation failed for call {call_id}: {e}")

    if not guidance:
        if risk_level == "critical":
            guidance = (
                "Based on what you told us, this has been marked urgent. Your ASHA worker "
                "and hospital are being alerted right now. Please seek medical attention "
                "immediately."
            )
        elif risk_level == "warning":
            guidance = (
                "Based on what you told us, please rest, stay hydrated, and take it easy. "
                "Your ASHA worker will follow up with you soon."
            )
        else:
            guidance = "Thank you. Your care team has this information and will follow up if needed."
    await _speak_then_hangup(call_control_id, guidance)


@router.post("/webhook/events")
async def handle_call_control_event(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Telnyx Call Control webhook — JSON event-driven, used for calls
    placed via the native /v2/calls API (calls/providers/telnyx.py). This
    is the path actually used for real Telnyx calls; the TeXML endpoints
    above remain for Twilio (PUBLIC_BASE_URL webhook mode) and as a
    reference TeXML implementation.

    NOT yet verified against a real live call — built and reasoned from
    Telnyx's documented event/action shapes, each individually confirmed via
    safe (non-call-placing) API tests during development, but the full
    sequence hasn't been run end-to-end against an actual phone call yet.
    """
    event = (payload or {}).get("data", {}) or {}
    event_type = event.get("event_type")
    p = event.get("payload", {}) or {}
    call_control_id = p.get("call_control_id")
    logger.info(f"Telnyx event received: {event_type} for {call_control_id}")

    if not call_control_id:
        return {"received": True}

    call = await _find_active_call(db, provider_call_id=call_control_id, to_number=p.get("to"))
    if not call:
        logger.warning(f"Telnyx event {event_type} for {call_control_id} did not match any known Call row")
        return {"received": True}

    if event_type == "call.answered":
        call.status = "in_progress"
        await db.commit()
        await _cc_action(call_control_id, "gather_using_speak", {
            "payload": (
                "Hello, this is SETU calling for your daily health check-in. "
                "Press 1 if you are feeling fine today. "
                "Press 2 to report symptoms. "
                "Press 3 if this is an emergency."
            ),
            "voice": "female",
            "language": "en-US",
            "minimum_digits": 1,
            "maximum_digits": 1,
            "timeout_millis": 8000,
            # Telnyx's own default is 3 — it silently REPLAYS the payload
            # (the whole greeting) that many times before ever firing
            # call.gather.ended if it doesn't detect a matching digit each
            # round. Confirmed live: this is exactly what read as "it kept
            # going back to hello this is setu" — not a bug in our own
            # timeout/fallback logic, Telnyx was retrying on its own,
            # invisibly to our webhook, for up to ~24s (3 x 8s) first. One
            # try only — our own "else" branch below already provides the
            # single graceful fallback we want.
            "maximum_tries": 1,
        })

    elif event_type == "call.gather.ended":
        # Same claim-then-defer fix as call.recording.saved below: digits
        # "1" and "3" call Gemini (via process_clinical_input) before
        # responding, which risks the same slow-ack-causes-retry failure
        # mode. dtmf_input starts NULL and this is the only place that ever
        # sets it, so "already set" (including to "" for a timeout) reliably
        # means an earlier delivery of this same event already claimed it.
        if call.dtmf_input is not None:
            return {"received": True}

        digits = p.get("digits") or ""
        call.dtmf_input = digits
        await db.commit()

        asyncio.create_task(_process_gather_ended(call.id, call_control_id, digits))

    elif event_type == "call.recording.saved":
        # Telnyx retransmits a webhook it doesn't get a fast ack for — and
        # this handler used to do audio-fetch + Sarvam + two Gemini calls
        # (~15-20s) BEFORE responding. Confirmed live: that's slow enough
        # that Telnyx retried the same event 2-3 times, running the whole
        # pipeline that many times in parallel, with one retry's `hangup`
        # landing mid-playback of another retry's `speak` — the exact
        # "cut off abruptly mid-sentence" symptom reported. Fix: claim the
        # event synchronously (fast, idempotent) and do all the slow work in
        # a background task using its own DB session, so the HTTP response
        # returns immediately regardless of how long transcription/Gemini
        # take.
        if call.recording_url:
            return {"received": True}  # already claimed by an earlier delivery of this same event

        recording_urls = p.get("recording_urls") or {}
        recording_url = recording_urls.get("mp3") or recording_urls.get("wav")
        if not recording_url:
            return {"received": True}

        call.recording_url = recording_url
        await db.commit()

        asyncio.create_task(_process_recording_saved(call.id, call_control_id, recording_url))

    elif event_type == "call.speak.ended":
        if p.get("client_state") == _HANGUP_AFTER_SPEAK:
            await _cc_action(call_control_id, "hangup", {})

    elif event_type == "call.hangup":
        call.status = "completed"
        await db.commit()

    return {"received": True}


@router.get("/ivr/flows")
async def list_ivr_flows():
    """List available IVR flows"""
    return {
        "flows": [
            {"id": "checkin", "name": "Check-in Flow"},
            {"id": "reminder", "name": "Medication Reminder Flow"},
            {"id": "emergency", "name": "Emergency Flow"},
        ]
    }
