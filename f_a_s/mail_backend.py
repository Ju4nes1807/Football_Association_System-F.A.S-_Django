import ssl
from django.core.mail.backends.smtp import EmailBackend

class AzureUnsafeEmailBackend(EmailBackend):
    """
    Backend de correo personalizado para solucionar el bug de 
    certificados SSL locales no encontrados en entornos Azure + Windows.
    """
    def open(self):
        if self.connection:
            return False
        try:
            # Forzamos un contexto SSL que NO valide el emisor local roto
            context = ssl._create_unverified_context()
            
            # Inicializamos la conexión SMTP_SSL clásica para el puerto 465
            self.connection = self.connection_class(
                self.host, 
                self.port, 
                timeout=self.timeout, 
                context=context
            )
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except:
            if not self.fail_silently:
                raise
            return False