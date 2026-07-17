"""Bot de WhatsApp (Meta Cloud API) para registrar treinos por chat.

Fluxo: a pessoa gera um código de 6 dígitos na página /whatsapp do site e o
envia para o número do bot — isso vincula o WhatsApp dela à conta (nenhuma
senha circula pelo chat). Depois, "treinar" inicia o registro guiado:
o bot pergunta série a série e grava tudo no histórico normal do site.

Variáveis de ambiente:
  WA_TOKEN            token permanente da Cloud API (sem ele, respostas só
                      vão para o log — útil em desenvolvimento)
  WA_PHONE_NUMBER_ID  id do número do bot no painel da Meta
  WA_VERIFY_TOKEN     string à sua escolha, usada na verificação do webhook
  WA_APP_SECRET       app secret da Meta (valida a assinatura das requisições)
  SITE_URL            endereço público do site, usado nas mensagens
"""

import hashlib
import hmac
import json
import os
import re
from datetime import date, datetime

import requests
from flask import Blueprint, current_app, jsonify, request

from models import (
    Measurement,
    SetLog,
    WhatsAppChatState,
    WhatsAppLink,
    WhatsAppLinkCode,
    WorkoutPlan,
    WorkoutSession,
    db,
)

wa = Blueprint("wa", __name__)

GRAPH_URL = "https://graph.facebook.com/v20.0"

HELP_TEXT = (
    "💪 *FitTracker Bot*\n"
    "Comandos:\n"
    "• *treinar* — registrar um treino da sua ficha\n"
    "• *peso 78,5* — registrar seu peso corporal\n"
    "• *historico* — seus últimos treinos\n"
    "• *cancelar* — descartar o registro em andamento\n"
    "Durante o treino, responda cada série com *reps peso* (ex.: 10 40)."
)


def site_url():
    return os.environ.get("SITE_URL", "https://fit-tracker-9z2h.onrender.com")


def send_message(to, text):
    token = os.environ.get("WA_TOKEN")
    phone_id = os.environ.get("WA_PHONE_NUMBER_ID")
    if not token or not phone_id:
        current_app.logger.info("[WA-SIM] para %s: %s", to, text)
        return
    try:
        requests.post(
            f"{GRAPH_URL}/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text},
            },
            timeout=15,
        )
    except requests.RequestException:
        current_app.logger.exception("Falha ao enviar mensagem ao WhatsApp")


# ------------------------------------------------------------ estado


def get_state(phone):
    row = db.session.get(WhatsAppChatState, phone)
    if row and row.state:
        try:
            return json.loads(row.state)
        except ValueError:
            pass
    return {}


def set_state(phone, state):
    row = db.session.get(WhatsAppChatState, phone)
    if not row:
        row = WhatsAppChatState(phone_number=phone)
        db.session.add(row)
    row.state = json.dumps(state)
    row.updated_at = datetime.utcnow()
    db.session.commit()


# ------------------------------------------------------------ webhook


def signature_ok(req):
    secret = os.environ.get("WA_APP_SECRET")
    if not secret:
        return True
    received = req.headers.get("X-Hub-Signature-256", "")
    expected = (
        "sha256=" + hmac.new(secret.encode(), req.get_data(), hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(received, expected)


@wa.route("/webhook/whatsapp", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.mode") == "subscribe" and request.args.get(
        "hub.verify_token"
    ) == os.environ.get("WA_VERIFY_TOKEN"):
        return request.args.get("hub.challenge", ""), 200
    return "token de verificação inválido", 403


@wa.route("/webhook/whatsapp", methods=["POST"])
def receive_webhook():
    if not signature_ok(request):
        return "assinatura inválida", 403
    data = request.get_json(silent=True) or {}
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                phone = msg.get("from", "")
                try:
                    if msg.get("type") != "text":
                        send_message(phone, "Por enquanto só entendo mensagens de texto 🙂")
                        continue
                    handle_message(phone, msg["text"]["body"])
                except Exception:
                    current_app.logger.exception("Erro ao processar mensagem de %s", phone)
                    db.session.rollback()
                    send_message(
                        phone, "Ops, algo deu errado aqui. Tente de novo em instantes."
                    )
    # Sempre 200: a Meta reenvia eventos que não recebem confirmação.
    return jsonify(status="ok")


# ------------------------------------------------------------ conversa


def handle_message(phone, text):
    text = (text or "").strip()
    link = WhatsAppLink.query.filter_by(phone_number=phone).first()
    if not link:
        handle_unlinked(phone, text)
        return
    handle_linked(link.user, phone, text)


def handle_unlinked(phone, text):
    if re.fullmatch(r"\d{6}", text):
        code = (
            WhatsAppLinkCode.query.filter(
                WhatsAppLinkCode.code == text,
                WhatsAppLinkCode.expires_at > datetime.utcnow(),
            )
            .order_by(WhatsAppLinkCode.id.desc())
            .first()
        )
        if code:
            user_name = code.user.name
            WhatsAppLink.query.filter_by(user_id=code.user_id).delete()
            db.session.add(WhatsAppLink(user_id=code.user_id, phone_number=phone))
            WhatsAppLinkCode.query.filter_by(user_id=code.user_id).delete()
            db.session.commit()
            send_message(
                phone,
                f"✅ WhatsApp vinculado à conta *{user_name}*!\n\n" + HELP_TEXT,
            )
            return
    send_message(
        phone,
        "Este número ainda não está vinculado a nenhuma conta.\n"
        f"Acesse {site_url()}/whatsapp, gere seu código de 6 dígitos "
        "e envie ele aqui.",
    )


def handle_linked(user, phone, text):
    t = text.lower().strip()
    state = get_state(phone)
    mode = state.get("mode")

    if t == "cancelar":
        set_state(phone, {})
        send_message(phone, "Registro cancelado. Quando quiser, mande *treinar*. 👍")
        return

    if mode == "logging":
        handle_logging(user, phone, state, t)
        return

    if mode == "choosing_plan":
        handle_plan_choice(user, phone, state, t)
        return

    if t in ("treinar", "treino"):
        start_training(user, phone)
    elif t.startswith("peso"):
        log_body_weight(user, phone, t)
    elif t in ("historico", "histórico"):
        send_history(user, phone)
    else:
        send_message(phone, HELP_TEXT)


def start_training(user, phone):
    plans = [
        p
        for p in WorkoutPlan.query.filter_by(user_id=user.id, active=True).all()
        if p.exercises
    ]
    if not plans:
        send_message(
            phone,
            "Você não tem fichas ativas com exercícios. "
            f"Monte uma em {site_url()}/fichas e volte aqui!",
        )
        return
    lines = [f"{i + 1}. {p.name} ({len(p.exercises)} exercícios)" for i, p in enumerate(plans)]
    set_state(phone, {"mode": "choosing_plan", "plan_ids": [p.id for p in plans]})
    send_message(
        phone,
        "Qual treino você vai fazer hoje? Responda com o número:\n" + "\n".join(lines),
    )


def handle_plan_choice(user, phone, state, t):
    plan_ids = state.get("plan_ids", [])
    if not (t.isdigit() and 1 <= int(t) <= len(plan_ids)):
        send_message(
            phone,
            f"Responda com o número da ficha (1 a {len(plan_ids)}), ou *cancelar*.",
        )
        return
    plan = db.session.get(WorkoutPlan, plan_ids[int(t) - 1])
    if not plan or plan.user_id != user.id:
        set_state(phone, {})
        send_message(phone, "Não encontrei essa ficha. Mande *treinar* para recomeçar.")
        return
    exs = [
        {
            "id": ex.id,
            "name": ex.name,
            "sets": ex.target_sets or 3,
            "reps": ex.target_reps or "?",
        }
        for ex in plan.exercises
    ]
    state = {
        "mode": "logging",
        "plan_id": plan.id,
        "plan_name": plan.name,
        "date": date.today().isoformat(),
        "exs": exs,
        "ex_i": 0,
        "set_n": 1,
        "logged": [],
    }
    set_state(phone, state)
    send_message(
        phone,
        f"🔥 Bora! *{plan.name}* — {len(exs)} exercícios.\n"
        "A cada série, responda *reps peso* (ex.: 10 40). "
        "Também aceito *pular* (próximo exercício), *finalizar* e *cancelar*.\n\n"
        + prompt_current(state),
    )


def prompt_current(state):
    ex = state["exs"][state["ex_i"]]
    return (
        f"🏋️ *{ex['name']}* — série {state['set_n']}/{ex['sets']} "
        f"(meta: {ex['reps']} reps)"
    )


def handle_logging(user, phone, state, t):
    if t in ("finalizar", "parar", "fim"):
        finish_session(user, phone, state)
        return
    if t == "pular":
        state["ex_i"] += 1
        state["set_n"] = 1
        if state["ex_i"] >= len(state["exs"]):
            finish_session(user, phone, state)
            return
        set_state(phone, state)
        send_message(phone, "Pulado. ➡️\n\n" + prompt_current(state))
        return

    m = re.fullmatch(r"(\d+)(?:\s*[x,;\s]\s*(\d+(?:[.,]\d+)?))?\s*(?:kg)?", t)
    if not m:
        send_message(
            phone,
            "Não entendi 😅 Responda *reps peso* (ex.: 10 40), só as reps (ex.: 12), "
            "ou *pular* / *finalizar* / *cancelar*.\n\n" + prompt_current(state),
        )
        return

    reps = int(m.group(1))
    weight = float(m.group(2).replace(",", ".")) if m.group(2) else None
    ex = state["exs"][state["ex_i"]]
    state["logged"].append(
        {
            "ex_id": ex["id"],
            "name": ex["name"],
            "set": state["set_n"],
            "reps": reps,
            "weight": weight,
        }
    )

    done = f"✔ {ex['name']} série {state['set_n']}: {reps} reps" + (
        f" × {weight:g} kg" if weight is not None else ""
    )

    state["set_n"] += 1
    if state["set_n"] > ex["sets"]:
        state["ex_i"] += 1
        state["set_n"] = 1
    if state["ex_i"] >= len(state["exs"]):
        send_message(phone, done)
        finish_session(user, phone, state)
        return

    set_state(phone, state)
    send_message(phone, done + "\n\n" + prompt_current(state))


def finish_session(user, phone, state):
    logged = state.get("logged", [])
    set_state(phone, {})
    if not logged:
        send_message(phone, "Nenhuma série registrada — nada foi salvo. Até a próxima!")
        return
    session = WorkoutSession(
        user_id=user.id,
        plan_id=state.get("plan_id"),
        date=date.fromisoformat(state["date"]),
        notes="Registrado pelo WhatsApp",
    )
    db.session.add(session)
    volume = 0.0
    for item in logged:
        volume += (item["reps"] or 0) * (item["weight"] or 0)
        db.session.add(
            SetLog(
                session=session,
                plan_exercise_id=item["ex_id"],
                exercise_name=item["name"],
                set_number=item["set"],
                reps=item["reps"],
                weight_kg=item["weight"],
            )
        )
    db.session.commit()
    send_message(
        phone,
        f"🎉 Treino salvo! *{state.get('plan_name', '')}*\n"
        f"• {len(logged)} séries\n"
        f"• volume total: {volume:g} kg\n"
        f"Veja sua evolução em {site_url()}/progresso 💪",
    )


def log_body_weight(user, phone, t):
    m = re.search(r"(\d+(?:[.,]\d+)?)", t)
    if not m:
        send_message(phone, "Para registrar o peso, mande por exemplo: *peso 78,5*")
        return
    weight = float(m.group(1).replace(",", "."))
    db.session.add(Measurement(user_id=user.id, date=date.today(), weight_kg=weight))
    db.session.commit()
    extra = ""
    if user.height_cm:
        h = user.height_cm / 100
        extra = f" (IMC {weight / (h * h):.1f})"
    send_message(phone, f"⚖️ Peso de {weight:g} kg registrado{extra}. Bom trabalho!")


def send_history(user, phone):
    sessions = (
        WorkoutSession.query.filter_by(user_id=user.id)
        .order_by(WorkoutSession.date.desc(), WorkoutSession.id.desc())
        .limit(3)
        .all()
    )
    if not sessions:
        send_message(phone, "Você ainda não registrou treinos. Mande *treinar*! 💪")
        return
    lines = [
        f"• {s.date.strftime('%d/%m')} — {s.plan.name if s.plan else 'Treino livre'}: "
        f"{len(s.set_logs)} séries, {s.total_volume:g} kg"
        for s in sessions
    ]
    send_message(
        phone,
        "🗓️ Seus últimos treinos:\n"
        + "\n".join(lines)
        + f"\nHistórico completo: {site_url()}/historico",
    )
