Instrucciones de instalación Loquendo Twitch Chat

	- Ingresar a https://twitchapps.com/tmi/ y dale a Connect.
	- Realizar login en Twitch, si ya estas logueado, se saltará esta parte.
	- Copia el código que aparece despues de oauth:
	- Abrir el archivo config.yaml con cualquier editor de texto.
	- En TWITCH_OAUTH_TOKEN, pegar el token copiado del paso anterior.
	- En TWITCH_CHANNEL, tu nombre de usuario de Twitch (en minusculas).
	- [Opcional] En IGNORED_USERS, los usuarios en el chat que seran ignorados (tipicamente los bots como Streamelements o Nightbot o los mensajes del streamer).
	- [Opcional] En IGNORED_MESSAGES_STARTS_WITH, los mensajes que comiencen con este texto serán ignorados (por ejemplo links o comandos).
	- Guardar el archivo.


Instrucciones de uso

	- Abrir LoquendoTwitch.exe
	- Espera a que haga login en Twitch y unos segundos más para que autentique en el servidor de las voces
	- Selecciona en Salida de Audio el dispositivo donde quieres que suene la voz
	- Y en Control de Volumen puedes seleccionar el volumen
	- Y listo! Pidele a tus viewers que escriban en el chat
	
	- Los viewers en el chat pueden cambiar su voz con el comando !voz [nombre de voz]. Por ejemplo: !voz Carlos.
	- Voces disponibles Carlos, Jorge, Diego, Javier, PaulinaMl, Angelica, Isabela, Francisca, Soledad.
	
	
- Si cierras el programa y lo vuelves a abrir, todas las configuraciones y opciones se mantienen.
- La ventana tambien muestra logs en donde se detallan las acciones del programa, y posibles errores.
- Por seguridad, las configs de token de Twitch estan en el config.yaml para que no se muestre en la ventana, NUNCA MOSTRAR ESTE TOKEN NI COMPARTIRLO.
