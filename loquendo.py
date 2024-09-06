import requests
import time
import json
import base64
import wave
from datetime import datetime
import threading
import sys


class Loquendo:
    def __init__(self, log_callback=None):
        self.session = requests.Session()
        self.headers = {
            "user-agent": "PostmanRuntime/7.37.3",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "connection": "keep-alive",
            "Cookie": "AWSALB=t4cqRO8QDNPjvFX1cnfjSJr7h7LU1AQ+6QwpYamc1oj5yHct51znARozVNyGI/Scx1/ZcJ9XtdPB2TidcdGueD6QEuYGFZEgUXujSQpDK7zSipZRNGnfKTc3cnAO"
        }
        self.session.headers.update(self.headers)
        self.log_callback = log_callback
        self.token = None
        self.first = True
        self.first1 = True
 

        refresh_thread = threading.Thread(target=self.refresh_token_thread, daemon=True)
        refresh_thread.start()
        
    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def _get_token(self):
        token_url = 'https://www.nuance.com/bin/nuance/ttstoken.json'

        while True:
            try:
                if self.first1:
                    self._log("⏳ [1/3] Servidor de voces: Autenticando...")
    #                self.bot.start_circle("red", 0)
    #                self.bot.stop_circle("yellow", 0)
    #                self.bot.stop_circle("green", 0)
                    self.first1 = False
                else:
                    print("Solicitando token TTS...")

                token_response = self.session.post(token_url)
                token_response.raise_for_status()

                if token_response.headers.get('Content-Type') == 'application/json;charset=utf-8':
                    token_data = token_response.json()
                    self.token = token_data.get("token")
                    if self.token:
                        last_token_time = time.time()  # Actualiza el tiempo del último token obtenido
                        print("Token TTS obtenido.")
                        break
                    else:
                        self._log(f"Error de conexion con el servidor de voces")
                        self._log("Reintentando...")
                        raise ValueError("Token no encontrado en la respuesta")
                        
                else:
                    self._log(f"Error de conexion con el servidor de voces")
                    self._log("Reintentando...")
                    print("Token no es un JSON, reintentando...")
            except Exception as err:
                self._log(f"Error de conexion con el servidor de voces")
                print(f"Error al obtener el token: {err}")
                self._log("Reintentando...")
                print("Reintentando...")
                time.sleep(1)  # Espera 300 ms antes de reintentar

    def refresh_token_thread(self):
        while True:
            try:
                if self.first:
                    print("1")
                self._get_token()
                if self.first:
        #            self.bot_instance.start_circle("green", 0)
        #           self.bot_instance.stop_circle("red", 0)
        #            self.bot_instance.stop_circle("yellow", 0)
       #             bot_instance.blink_yellow_circle([0, 1, 2])
                    self._log("✔ [2/3] Servidor de voces: Conectado")
                    ok_voice = True
                    self.first = False
                time.sleep(15)  # Esperar 15 segundos antes de refrescar el token
            except Exception as e:
                print(f"Error al actualizar el token: {e}")
                self._log(f"Error al actualizar el token: {e}")

    def tts(self, texto, voz, archivo_salida=None):
        s = {
            "texto": texto,
            "voz": voz,
            "idioma": None,
            "modelo": "standard",
            "sample_rate": 22050,
            "archivo_salida": archivo_salida,
            "tiempo": None,
            "res": None,
        }
        inicio = time.time()

        if not archivo_salida:
            fecha_hora_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            s["archivo_salida"] = f'{s["voz"]}_{s["modelo"]}_{fecha_hora_actual}.wav'

        url = 'https://tts.api.nuance.com/api/v1/synthesize'
        data = {
            "voice": {
                "name": s["voz"],
                "model": s["modelo"]
            },
            "input": {
                "text": {
                    "text": s["texto"]
                }
            }
        }
        try:
            print("Solicitud enviada a Nuance TTS API:")
            print("URL: " + url)
            print("Datos enviados: " + json.dumps(data))

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            req = self.session.post(url, json=data, headers=headers)

            req.raise_for_status()

            audio64 = req.json()["audio"]
            bytes_audio = base64.b64decode(audio64)
            with wave.open(s["archivo_salida"], "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(22050)
                f.writeframes(bytes_audio)
            s["tiempo"] = time.time() - inicio
            s["res"] = "OK"
        except Exception as err:
            s["res"] = f'ERROR: {err}'
            if '401' in str(err):
                print("No autenticado con el servidor de voces: " + str(err))
                self._log("No autenticado con el servidor de voces")
            else:
                print("Error al generar el archivo de audio: " + str(err))
                self._log("Error al generar el archivo de audio: " + str(err))


        return s
    
