import requests
import time
import json
import base64
import wave
from datetime import datetime
import threading

class Loquendo:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "user-agent": "PostmanRuntime/7.37.3",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "connection": "keep-alive",
            "Cookie": "AWSALB=t4cqRO8QDNPjvFX1cnfjSJr7h7LU1AQ+6QwpYamc1oj5yHct51znARozVNyGI/Scx1/ZcJ9XtdPB2TidcdGueD6QEuYGFZEgUXujSQpDK7zSipZRNGnfKTc3cnAO"
        }
        self.session.headers.update(self.headers)
        self.token = None
        self._get_token()
        
        # Iniciar el hilo para refrescar el token cada 15 segundos
        self.token_refresh_thread = threading.Thread(target=self._refresh_token_thread, daemon=True)
        self.token_refresh_thread.start()

    def _get_token(self):
        token_url = 'https://www.nuance.com/bin/nuance/ttstoken.json'

        while True:
            try:
                print("Requesting token...")
                token_response = self.session.post(token_url)
                token_response.raise_for_status()
                print("Content-Type:", token_response.headers.get('Content-Type'))

                if token_response.headers.get('Content-Type') == 'application/json;charset=utf-8':
                    token_data = token_response.json()
                    self.token = token_data.get("token")
                    if self.token:
                        last_token_time = time.time()  # Actualiza el tiempo del último token obtenido
                        print("Token obtained successfully.")
                        break
                    else:
                        raise ValueError("Token not found in the response")
                else:
                    print("Token response is not JSON, retrying...")
            except Exception as err:
                print(f"Error while getting token: {err}")
                print("Retrying...")
                time.sleep(0.3)  # Espera 300 ms antes de reintentar

            # Comprueba si el token ha expirado

    def _refresh_token_thread(self):
        while True:
            time.sleep(60)  # Esperar 15 segundos antes de refrescar el token
            try:
                self._get_token()
            except Exception as e:
                print(f"Error while refreshing token: {e}")

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
            print("URL:", url)
            print("Datos enviados:", json.dumps(data))

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
            print("Error al generar el archivo de audio:", err)

        return s
