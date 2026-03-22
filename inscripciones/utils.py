from datetime import date
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.conf import settings


RANGOS_CATEGORIA = {
    'SUB8':  (5, 8),
    'SUB10': (9, 10),
    'SUB12': (11, 12),
    'SUB14': (13, 14),
    'SUB16': (15, 16),
    'SUB18': (17, 18),
    'MAYOR': (19, 99),
}

def calcular_edad(fecha_nacimiento):
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad

def validar_edad_categoria(fecha_nacimiento, categoria):
    edad = calcular_edad(fecha_nacimiento)
    min_edad, max_edad = RANGOS_CATEGORIA.get(categoria, (0, 99))
    if not (min_edad <= edad <= max_edad):
        return False, f'El jugador tiene {edad} años. La categoria {categoria} acepta entre {min_edad} y {max_edad} años.'
    return True, None

def _enviar_credenciales_jugador(jugador, password_plana, request):
    """Envía las credenciales de acceso al jugador por correo."""
    from django.core.mail import EmailMultiAlternatives
    from django.urls import reverse
    
    login_url = request.build_absolute_uri(reverse('login'))
    asunto = '🎉 Bienvenido a F.A.S — Tus credenciales de acceso'

    texto_plano = f"""
Hola {jugador.nombres} {jugador.apellidos},

Has sido registrado en el sistema F.A.S (Football Association System).

Correo:     {jugador.email}
Contraseña: {password_plana}

Equipo:    {jugador.equipo.nombre}
Categoría: {jugador.equipo.categoria_display}
Dorsal:    #{jugador.dorsal}
Posición:  {jugador.posicion.title()}

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
                <h2 style="margin:0 0 8px;color:#0d47a1;font-size:22px;">
                  ¡Bienvenido, {jugador.nombres}! ⚽
                </h2>
                <p style="margin:0;color:#555;font-size:15px;line-height:1.6;">
                  Has sido registrado como <strong>Jugador</strong> en F.A.S.
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
                          <td style="color:#1a1a1a;font-size:14px;font-weight:600;padding:6px 0;">{jugador.email}</td>
                        </tr>
                        <tr>
                          <td style="color:#777;font-size:13px;padding:6px 0;">Contraseña</td>
                          <td style="padding:6px 0;">
                            <span style="background:#1a73e8;color:#fff;font-size:15px;font-weight:700;
                                         padding:4px 14px;border-radius:6px;letter-spacing:1px;
                                         font-family:monospace;">{password_plana}</span>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- INFO DEPORTIVA -->
            <tr>
              <td style="padding:0 40px 28px;">
                <table width="100%" cellpadding="0" cellspacing="0"
                       style="background:#f0fff4;border-radius:12px;border:1px solid #a7f3d0;">
                  <tr>
                    <td style="padding:20px 24px;">
                      <p style="margin:0 0 14px;font-size:13px;font-weight:700;
                                color:#059669;text-transform:uppercase;letter-spacing:.8px;">
                        ⚽ Tu información deportiva
                      </p>
                      <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                          <td style="width:110px;color:#777;font-size:13px;padding:5px 0;">Equipo</td>
                          <td style="color:#1a1a1a;font-size:14px;font-weight:600;padding:5px 0;">{jugador.equipo.nombre}</td>
                        </tr>
                        <tr>
                          <td style="color:#777;font-size:13px;padding:5px 0;">Categoría</td>
                          <td style="color:#1a1a1a;font-size:14px;padding:5px 0;">{jugador.equipo.categoria_display}</td>
                        </tr>
                        <tr>
                          <td style="color:#777;font-size:13px;padding:5px 0;">Dorsal</td>
                          <td style="color:#1a1a1a;font-size:14px;font-weight:700;padding:5px 0;">#{jugador.dorsal}</td>
                        </tr>
                        <tr>
                          <td style="color:#777;font-size:13px;padding:5px 0;">Posición</td>
                          <td style="color:#1a1a1a;font-size:14px;padding:5px 0;">{jugador.posicion.title()}</td>
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

    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=texto_plano,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[jugador.email],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send()
    except Exception:
        pass