
# ── CKRPRO API HOMEPAGE ──
from flask import render_template_string


@app.route("/", methods=["GET"])
def home():
    base = request.url_root.rstrip("/")

    endpoints = [
        {
            "path": "/health",
            "description": "Check API and bot connection",
            "example": "/health",
        },
        {
            "path": "/3?uid=PLAYER_UID",
            "description": "3-player squad invite",
            "example": "/3?uid=PLAYER_UID",
        },
        {
            "path": "/5?uid=PLAYER_UID",
            "description": "5-player squad invite",
            "example": "/5?uid=PLAYER_UID",
        },
        {
            "path": "/6?uid=PLAYER_UID",
            "description": "6-player squad invite",
            "example": "/6?uid=PLAYER_UID",
        },
        {
            "path": "/emote?uid1=PLAYER_UID&emote_id=EMOTE_ID",
            "description": "Send emote to selected UIDs",
            "example": "/emote?uid1=PLAYER_UID&emote_id=EMOTE_ID",
        },
        {
            "path": "/join?tc=TEAM_CODE&uid1=PLAYER_UID&emote_id=EMOTE_ID",
            "description": "Join squad, send emote and leave",
            "example": "/join?tc=TEAM_CODE&uid1=PLAYER_UID&emote_id=EMOTE_ID",
        },
    ]

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="theme-color" content="#080b10">
      <title>CKRPRO FF API</title>

      <style>
        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          padding: 18px;
          background: #080b10;
          color: #f3f4f6;
          font-family: Arial, Helvetica, sans-serif;
        }

        main {
          width: 100%;
          max-width: 680px;
          margin: 22px auto;
        }

        .header {
          background: #0d1219;
          padding: 22px;
          border-radius: 16px;
          margin-bottom: 18px;
        }

        h1 {
          margin: 0;
          color: #19d77b;
          font-size: 25px;
          font-weight: 800;
        }

        .subtitle {
          color: #aab4c2;
          font-size: 14px;
          line-height: 1.6;
          margin: 10px 0;
        }

        .server {
          display: inline-block;
          padding: 7px 10px;
          background: #13241d;
          color: #19d77b;
          border-radius: 8px;
          font-size: 12px;
          font-weight: bold;
        }

        .base {
          margin-top: 15px;
          color: #aab4c2;
          font-size: 12px;
          overflow-wrap: anywhere;
        }

        a {
          color: #22c7e8;
          text-decoration: none;
        }

        .health-link {
          display: inline-block;
          margin-top: 12px;
          padding: 10px 13px;
          background: #19d77b;
          color: #06120b;
          border-radius: 9px;
          font-size: 13px;
          font-weight: bold;
        }

        h2 {
          font-size: 15px;
          margin: 22px 0 12px;
        }

        .endpoint {
          background: #0d1219;
          border-radius: 12px;
          padding: 15px;
          margin-bottom: 10px;
        }

        .method {
          color: #19d77b;
          font-size: 11px;
          font-weight: bold;
          margin-bottom: 9px;
        }

        .path {
          color: #f3f4f6;
          font-size: 13px;
          font-weight: bold;
          line-height: 1.7;
          overflow-wrap: anywhere;
        }

        .description {
          color: #9ca8b8;
          font-size: 12px;
          line-height: 1.5;
          margin-top: 7px;
        }

        .open {
          display: inline-block;
          margin-top: 12px;
          font-size: 12px;
          font-weight: bold;
        }

        footer {
          text-align: center;
          padding: 25px 0 10px;
          color: #748091;
          font-size: 11px;
        }

        @media (max-width: 420px) {
          body {
            padding: 12px;
          }

          main {
            margin-top: 10px;
          }

          .header {
            padding: 17px;
          }

          h1 {
            font-size: 22px;
          }
        }
      </style>
    </head>

    <body>
      <main>
        <section class="header">
          <h1>CKRPRO FF API</h1>

          <p class="subtitle">
            Free Fire API endpoint documentation.
            Check the service status and available routes below.
          </p>

          <div class="server">API DOCUMENTATION</div>

          <div class="base">
            BASE URL<br>
            <a href="{{ base }}">{{ base }}</a>
          </div>

          <a class="health-link" href="/health">
            CHECK API STATUS
          </a>
        </section>

        <h2>AVAILABLE ENDPOINTS</h2>

        {% for endpoint in endpoints %}
        <section class="endpoint">
          <div class="method">GET ENDPOINT</div>

          <div class="path">{{ endpoint.path }}</div>

          <div class="description">
            {{ endpoint.description }}
          </div>

          {% if endpoint.example == "/health" %}
          <a class="open" href="/health">OPEN STATUS →</a>
          {% else %}
          <div class="description">
            Replace the example values with valid parameters before use.
          </div>
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
        endpoints=endpoints
    )


# ── HEALTH CHECK ──
@app.route("/health", methods=["GET"])
def health():
    connected = _ready()

    return jsonify({
        "service": "CKRPRO FF API",
        "status": "online",
        "bot_connected": connected,
        "region": STATE.get("region"),
        "message": (
            "Bot connected"
            if connected
            else "Web service is running; bot is not ready"
        )
    }), 200
