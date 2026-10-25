
import os
import asyncio
import threading

from flask import Flask, request, jsonify, render_template_string

import bot


# ─────────────────────────────
# CONFIGURATION
# ─────────────────────────────

app = Flask(__name__)

LOOP = None
API_KEY = os.environ.get("API_KEY", "")
SQUAD_STAY_SECONDS = 8

STATE = {
    "key": None,
    "iv": None,
    "region": None,
    "uid": None,
    "client_version": "1.132.1",
}

_lock = None


# ─────────────────────────────
# CAPTURE LOGIN INFORMATION
# ─────────────────────────────

_orig_run_account = bot.run_account


async def _patched_run_account(account_data):
    STATE["key"] = account_data["aes_ak"]
    STATE["iv"] = account_data["iv_i"]
    STATE["region"] = account_data.get("region") or "SG"
    STATE["uid"] = int(account_data["account_id"])
    STATE["client_version"] = (
        account_data.get("client_version") or "1.132.1"
    )

    await _orig_run_account(account_data)


bot.run_account = _patched_run_account


# ─────────────────────────────
# HELPERS
# ─────────────────────────────

def _get_lock():
    global _lock

    if _lock is None:
        _lock = asyncio.Lock()

    return _lock


def _writer():
    try:
        writer = bot._online_writer_ref[0]

        if writer is not None and not writer.is_closing():
            return writer

    except (AttributeError, IndexError, TypeError):
        pass

    return None


def _ready():
    return (
        STATE["key"] is not None
        and STATE["iv"] is not None
        and _writer() is not None
    )


async def _send(packet):
    writer = _writer()

    if writer is None:
        raise RuntimeError("Bot online socket is not ready")

    writer.write(packet)
    await writer.drain()


def _resolve_emote(value):
    value = str(value or "").strip()

    if not value:
        return None

    if value.isdigit() and int(value) >= 1000:
        return int(value)

    try:
        return bot._find_emote(value)
    except (ValueError, TypeError, KeyError):
        return None


def _uids():
    result = []

    for number in range(1, 7):
        value = request.args.get(f"uid{number}")

        if value:
            if not value.isdigit():
                return None

            result.append(int(value))

    return result


def _auth_fail():
    if API_KEY and request.args.get("key") != API_KEY:
        return jsonify({
            "status": "error",
            "message": "Invalid API key",
        }), 401

    if LOOP is None or not LOOP.is_running():
        return jsonify({
            "status": "error",
            "message": "Bot event loop is not running",
        }), 503

    if not _ready():
        return jsonify({
            "status": "error",
            "message": "Bot is not connected yet",
        }), 503

    return None


def _run(coroutine, name):
    if LOOP is None or not LOOP.is_running():
        coroutine.close()
        raise RuntimeError("Bot event loop is not running")

    future = asyncio.run_coroutine_threadsafe(coroutine, LOOP)

    def completed(task):
        try:
            task.result()
            print(f"[API] {name}: completed")
        except Exception as error:
            print(f"[API] {name}: failed: {error}")

    future.add_done_callback(completed)


# ─────────────────────────────
# HOMEPAGE
# ─────────────────────────────

@app.route("/", methods=["GET"])
def home():
    base = request.url_root.rstrip("/")

    endpoints = [
        {
            "path": "/health",
            "description": "Check web service and bot connection",
            "example": "/health",
        },
        {
            "path": "/3?uid=PLAYER_UID",
            "description": "Send 3-player squad invite",
        },
        {
            "path": "/5?uid=PLAYER_UID",
            "description": "Send 5-player squad invite",
        },
        {
            "path": "/6?uid=PLAYER_UID",
            "description": "Send 6-player squad invite",
        },
        {
            "path": "/emote?uid1=PLAYER_UID&emote_id=EMOTE_ID",
            "description": "Send emote to selected player UIDs",
        },
        {
            "path": "/join?tc=TEAM_CODE&uid1=PLAYER_UID&emote_id=EMOTE_ID",
            "description": "Join squad, send emote and leave",
        },
    ]

    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="theme-color" content="#080b10">
      <title>CKRPRO FF API</title>

      <style>
        * { box-sizing: border-box; }

        body {
          margin: 0;
          padding: 16px;
          background: #080b10;
          color: #f3f4f6;
          font-family: Arial, sans-serif;
        }

        main {
          max-width: 680px;
          margin: 20px auto;
        }

        .header, .endpoint {
          background: #0d1219;
          border-radius: 13px;
          padding: 17px;
          margin-bottom: 12px;
        }

        h1 {
          color: #19d77b;
          font-size: 24px;
          margin: 0;
        }

        h2 {
          font-size: 14px;
          margin: 22px 0 12px;
        }

        p {
          color: #aab4c2;
          font-size: 13px;
          line-height: 1.6;
        }

        .base {
          overflow-wrap: anywhere;
          font-size: 12px;
          color: #22c7e8;
        }

        .badge {
          display: inline-block;
          color: #19d77b;
          background: #13241d;
          padding: 7px 9px;
          border-radius: 7px;
          font-size: 11px;
          font-weight: bold;
        }

        .method {
          color: #19d77b;
          font-size: 11px;
          font-weight: bold;
          margin-bottom: 8px;
        }

        .path {
          color: #fff;
          font-size: 13px;
          line-height: 1.6;
          overflow-wrap: anywhere;
          font-weight: bold;
        }

        .description {
          color: #9ca8b8;
          font-size: 12px;
          line-height: 1.6;
          margin-top: 7px;
        }

        a {
          color: #22c7e8;
          text-decoration: none;
        }

        .button {
          display: inline-block;
          margin-top: 8px;
          background: #19d77b;
          color: #06120b;
          padding: 10px 13px;
          border-radius: 8px;
          font-weight: bold;
          font-size: 12px;
        }

        footer {
          text-align: center;
          color: #748091;
          padding: 18px;
          font-size: 11px;
        }

        @media(max-width: 420px) {
          body { padding: 11px; }
          h1 { font-size: 21px; }
          .header, .endpoint { padding: 14px; }
        }
      </style>
    </head>

    <body>
      <main>
        <section class="header">
          <h1>CKRPRO FF API</h1>

          <p>Free Fire API endpoint documentation.</p>

          <span class="badge">API DOCUMENTATION</span>

          <p>BASE URL</p>
          <div class="base">{{ base }}</div>

          <a class="button" href="/health">CHECK STATUS</a>
        </section>

        <h2>AVAILABLE ENDPOINTS</h2>

        {% for endpoint in endpoints %}
        <section class="endpoint">
          <div class="method">GET ENDPOINT</div>
          <div class="path">{{ endpoint.path }}</div>
          <div class="description">{{ endpoint.description }}</div>

          {% if endpoint.example is defined %}
          <a href="{{ endpoint.example }}">OPEN ENDPOINT →</a>
          {% endif %}
        </section>
        {% endfor %}

        <footer>DEVELOPER: CKRPRO</footer>
      </main>
    </body>
    </html>
    """

    return render_template_string(
        html,
        base=base,
        endpoints=endpoints,
    )


# ─────────────────────────────
# HEALTH CHECK
# ─────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    connected = _ready()

    return jsonify({
        "service": "CKRPRO FF API",
        "web_status": "online",
        "bot_connected": connected,
        "region": STATE.get("region"),
        "message": (
            "Bot connected"
            if connected
            else "Web service is running; bot is not ready"
        ),
    }), 200


# ─────────────────────────────
# INVITE ACTIONS
# ─────────────────────────────

async def do_invite(size, uid):
    async with _get_lock():
        key = STATE["key"]
        iv = STATE["iv"]
        region = STATE["region"]

        await _send(
            bot.build_open_squad_packet(
                size, key, iv, region, STATE["client_version"]
            )
        )

        await asyncio.sleep(0.3)

        await _send(
            bot.build_invite_squad_packet(1, uid, key, iv, region)
        )

        await asyncio.sleep(0.2)

        await _send(
            bot.build_invite_squad_packet(2, uid, key, iv, region)
        )

        await asyncio.sleep(SQUAD_STAY_SECONDS)

        await _send(
            bot.build_leave_squad_packet(
                STATE["uid"], key, iv, region
            )
        )


def _invite_route(size):
    failure = _auth_fail()

    if failure:
        return failure

    value = request.args.get("uid", "")

    if not value.isdigit() or int(value) <= 0:
        return jsonify({
            "status": "error",
            "message": "A valid uid is required",
        }), 400

    try:
        _run(do_invite(size, int(value)), f"invite{size} {value}")
    except RuntimeError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 503

    return jsonify({
        "status": "success",
        "target_uid": int(value),
        "message": f"{size}-player invite queued",
    }), 200


@app.route("/3", methods=["GET"])
def r3():
    return _invite_route(3)


@app.route("/5", methods=["GET"])
def r5():
    return _invite_route(5)


@app.route("/6", methods=["GET"])
def r6():
    return _invite_route(6)


# ─────────────────────────────
# EMOTE ACTION
# ─────────────────────────────

async def do_emote(uids, emote_id):
    key = STATE["key"]
    iv = STATE["iv"]
    region = STATE["region"]

    for uid in uids:
        await _send(
            bot.build_emote_packet(
                STATE["uid"], int(uid), emote_id, key, iv, region
            )
        )
        await asyncio.sleep(0.05)


@app.route("/emote", methods=["GET"])
def r_emote():
    failure = _auth_fail()

    if failure:
        return failure

    uids = _uids()
    emote_id = _resolve_emote(request.args.get("emote_id", ""))

    if not uids or not emote_id:
        return jsonify({
            "status": "error",
            "message": "Valid uid1..uid6 and emote_id are required",
        }), 400

    try:
        _run(do_emote(uids, emote_id), f"emote {emote_id}")
    except RuntimeError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 503

    return jsonify({
        "status": "success",
        "uids": uids,
        "emote_id": emote_id,
        "message": "Emote request queued",
    }), 200


# ─────────────────────────────
# JOIN BY TEAM CODE
# ─────────────────────────────

def build_join_by_code_packet(code, key, iv, region, client_version):
    fields = {
        1: 4,
        2: {
            4: bytes.fromhex("01090a0b121920"),
            5: str(code),
            6: 6,
            8: 1,
            9: {
                2: 800,
                6: 11,
                8: str(client_version),
                9: 5,
                10: 1,
            },
        },
    }

    return bot._wrap_packet(
        bot._serialize(fields),
        bot._squad_prefix(5, region),
        key,
        iv,
    )


async def do_join_emote(code, uids, emote_id):
    async with _get_lock():
        key = STATE["key"]
        iv = STATE["iv"]
        region = STATE["region"]

        await _send(
            build_join_by_code_packet(
                code, key, iv, region, STATE["client_version"]
            )
        )

        await asyncio.sleep(0.6)

        await do_emote(uids, emote_id)

        await asyncio.sleep(0.3)

        await _send(
            bot.build_leave_squad_packet(
                STATE["uid"], key, iv, region
            )
        )


@app.route("/join", methods=["GET"])
def r_join():
    failure = _auth_fail()

    if failure:
        return failure

    code = (request.args.get("tc") or "").strip()
    uids = _uids()
    emote_id = _resolve_emote(request.args.get("emote_id", ""))

    if not code or not uids or not emote_id:
        return jsonify({
            "status": "error",
            "message": "tc, uid1..uid6 and a valid emote_id are required",
        }), 400

    try:
        _run(
            do_join_emote(code, uids, emote_id),
            f"join {code}",
        )
    except RuntimeError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 503

    return jsonify({
        "status": "success",
        "team_code": code,
        "uids": uids,
        "emote_id": emote_id,
        "message": "Join/emote request queued",
    }), 200


# ─────────────────────────────
# FLASK SERVER
# ─────────────────────────────

def run_flask():
    port = int(os.environ.get("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


# ─────────────────────────────
# START BOT
# ─────────────────────────────

def main():
    global LOOP

    creds = bot.read_credentials() or {}

    token = creds.get("access_token", "")
    uid = str(creds.get("uid", ""))
    password = creds.get("password", "")

    if not token and not (uid.isdigit() and password):
        print("ERROR: Add uid/password or access_token to ckr.txt")
        return

    LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(LOOP)

    bot.shutdown_requested = False

    threading.Thread(
        target=run_flask,
        daemon=True,
    ).start()

    async def runner():
        if token:
            await bot.run_token_account(token)
        else:
            await bot.run_forever(
                lambda: bot.run_guest_account(uid, password)
            )

    try:
        LOOP.run_until_complete(runner())
    except KeyboardInterrupt:
        bot.shutdown_requested = True
    finally:
        pending = asyncio.all_tasks(LOOP)

        for task in pending:
            task.cancel()

        if pending:
            LOOP.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )

        LOOP.close()


if __name__ == "__main__":
    main()
