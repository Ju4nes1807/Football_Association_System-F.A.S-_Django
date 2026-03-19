from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def enviar_credenciales_admin(nombre, email, password, login_url):
    asunto = '🎉 Bienvenido a F.A.S — Tus credenciales de acceso'

    texto_plano = f"""
Hola {nombre},

Has sido registrado como Administrador en F.A.S.

Correo:     {email}
Contraseña: {password}

Inicia sesión aquí: {login_url}

Por seguridad, cambia tu contraseña después del primer inicio de sesión.

— Equipo F.A.S
    """.strip()

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:40px 0;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="background:#fff;border-radius:16px;overflow:hidden;
                        box-shadow:0 4px 24px rgba(0,0,0,.10);max-width:600px;width:100%;">

            <!-- HEADER -->
            <tr>
              <td style="background:#1a73e8;padding:36px 40px;text-align:center;">
                <h1 style="margin:0;color:#fff;font-size:28px;font-weight:800;">F.A.S</h1>
                <p style="margin:6px 0 0;color:#e8f0fe;font-size:14px;">Football Association System</p>
              </td>
            </tr>

            <!-- BIENVENIDA -->
            <tr>
              <td style="padding:36px 40px 0;">
                <h2 style="margin:0 0 8px;color:#0d47a1;font-size:22px;">¡Bienvenido, {nombre}! 👋</h2>
                <p style="margin:0;color:#555;font-size:15px;line-height:1.6;">
                  Has sido registrado como <strong>Administrador</strong> en F.A.S.
                  Aquí están tus credenciales de acceso.
                </p>
              </td>
            </tr>

            <!-- CREDENCIALES -->
            <tr>
              <td style="padding:28px 40px;">
                <table width="100%" cellpadding="0" cellspacing="0"
                       style="background:#f0f4ff;border-radius:12px;border:1px solid #d0e0ff;">
                  <tr>
                    <td style="padding:20px 24px;">
                      <p style="margin:0 0 14px;font-size:13px;font-weight:700;
                                color:#1a73e8;text-transform:uppercase;letter-spacing:.8px;">
                        🔐 Tus credenciales
                      </p>
                      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px;">
                        <tr>
                          <td style="width:110px;color:#777;font-size:13px;padding:6px 0;">Correo</td>
                          <td style="color:#1a1a1a;font-size:14px;font-weight:600;padding:6px 0;">{email}</td>
                        </tr>
                      </table>
                      <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                          <td style="width:110px;color:#777;font-size:13px;padding:6px 0;">Contraseña</td>
                          <td style="padding:6px 0;">
                            <span style="background:#1a73e8;color:#fff;font-size:15px;font-weight:700;
                                         padding:4px 14px;border-radius:6px;letter-spacing:1px;
                                         font-family:monospace;">{password}</span>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- BOTÓN -->
            <tr>
              <td style="padding:0 40px 36px;text-align:center;">
                <a href="{login_url}"
                   style="display:inline-block;background:#1a73e8;color:#fff;
                          font-size:15px;font-weight:700;text-decoration:none;
                          padding:14px 40px;border-radius:10px;
                          box-shadow:0 4px 14px rgba(26,115,232,0.35);">
                  Iniciar sesión →
                </a>
              </td>
            </tr>

            <!-- AVISO -->
            <tr>
              <td style="padding:0 40px 32px;">
                <table width="100%" cellpadding="0" cellspacing="0"
                       style="background:#fff8e1;border-radius:10px;border-left:4px solid #ffb300;">
                  <tr>
                    <td style="padding:14px 18px;color:#7a5c00;font-size:13px;line-height:1.6;">
                      ⚠️ <strong>Por seguridad</strong>, cambia tu contraseña después
                      del primer inicio de sesión. No compartas estas credenciales.
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- FOOTER -->
            <tr>
              <td style="background:#f4f6f9;padding:20px 40px;text-align:center;
                         border-top:1px solid #e5e7eb;">
                <p style="margin:0;color:#9ca3af;font-size:12px;">
                  © Football Association System — Todos los derechos reservados
                </p>
              </td>
            </tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send()