import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import webbrowser
from flask import Flask, render_template_string, jsonify
import threading
import time


# Configuración de voz
recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Voz en español

# Nombre del asistente
nombre_asistente = "jarvis"
archivo_nombre = "nombre_usuario.txt"
estado_espera = False

# Obtener nombre de usuario
def obtener_nombre_usuario():
    try:
        with open(archivo_nombre, 'r') as file:
            nombre = file.read()
            if nombre:
                return nombre
    except FileNotFoundError:
        pass
    return None

# Establecer nombre de usuario
def establecer_nombre_usuario():
    global estado_espera
    hablar("Hola, soy Jarvis. ¿Cuál es tu nombre?")
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            estado_espera = True
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            estado_espera = False
            nombre = recognizer.recognize_google(audio, language='es')
            with open(archivo_nombre, 'w') as file:
                file.write(nombre)
            return nombre.lower()
        except sr.WaitTimeoutError:
            estado_espera = False
            return ""
        except sr.UnknownValueError:
            estado_espera = False
            return ""

def obtener_hora_actual():
    hora = datetime.datetime.now().strftime('%H:%M:%S')
    return hora

def obtener_saludo():
    hora = datetime.datetime.now().hour
    if 5 <= hora < 12:
        return "Buenos días"
    elif 12 <= hora < 18:
        return "Buenas tardes"
    else:
        return "Buenas noches"

def escuchar_comando():
    global estado_espera
    with sr.Microphone() as source:
        print("Te escucho...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            estado_espera = True
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            estado_espera = False
            texto = recognizer.recognize_google(audio, language='es')
            return texto.lower()
        except sr.WaitTimeoutError:
            estado_espera = False
            return ""
        except sr.UnknownValueError:
            estado_espera = False
            return ""

def hablar(texto):
    global talking
    talking = True
    engine.say(texto)
    engine.runAndWait()
    talking = False

def abrir_cuenta_google():
    url = "https://mail.google.com/mail/u/0/?ogbl#inbox"  # URL de Gmail
    webbrowser.open(url)
    hablar("Abriendo tu cuenta de Google.")

# HTML y JavaScript para la visualización
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis Visualizer</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #000;
        }
        canvas {
            border: 1px solid #fff;
        }
    </style>
</head>
<body>
    <canvas id="visualizer"></canvas>
    <script>
        let isWaitingForResponse = false;

        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const canvas = document.getElementById('visualizer');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;

            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = 150;

            function draw() {
                requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);

                ctx.clearRect(0, 0, canvas.width, canvas.height);

                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                ctx.strokeStyle = isWaitingForResponse ? 'green' : '#ffffff';
                ctx.stroke();

                const barWidth = (2 * Math.PI) / bufferLength;

                for (let i = 0; i < bufferLength; i++) {
                    const barHeight = dataArray[i] / 2;
                    const angle = i * barWidth;

                    const x1 = centerX + Math.cos(angle) * radius;
                    const y1 = centerY + Math.sin(angle) * radius;
                    const x2 = centerX + Math.cos(angle) * (radius + barHeight);
                    const y2 = centerY + Math.sin(angle) * (radius + barHeight);

                    ctx.strokeStyle = `rgb(${dataArray[i]}, 50, 50)`;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                }
            }

            draw();
        }).catch(err => {
            console.log('Error accessing microphone:', err);
        });

        // Polling server to check if waiting for response
        setInterval(() => {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    isWaitingForResponse = data.waiting;
                })
                .catch(err => console.error('Error fetching status:', err));
        }, 1000);
    </script>
</body>
</html>
'''

# Flask app para servir la página HTML y manejar el estado
app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/status')
def status():
    global estado_espera
    return jsonify(waiting=estado_espera)

def run_flask():
    app.run(debug=True, use_reloader=False)

# Hilo para ejecutar Flask
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Esperar un momento para que el servidor Flask inicie
time.sleep(2)

# Abrir la página web en el navegador
webbrowser.open("http://127.0.0.1:5000")

nombre_usuario = obtener_nombre_usuario()

if nombre_usuario:
    saludo = obtener_saludo()
    hora_actual = obtener_hora_actual()
    hablar(f"{saludo}, {nombre_usuario.capitalize()}! Son las {hora_actual}. ¿En qué puedo servirte?")
else:
    nombre_usuario = establecer_nombre_usuario()
    hablar(f"Mucho gusto, {nombre_usuario.capitalize()}.")

while True:
    comando = escuchar_comando()
    if nombre_asistente.lower() in comando:
        hablar("Sí señor, ¿en qué puedo ayudarte?")
        while True:
            comando = escuchar_comando()
            if nombre_asistente.lower() in comando:
                hablar("¿En qué más puedo ayudarle señor?")

            elif 'duerme' in comando:
                hablar("Durmiendo, si necesita de algo señor diga mi nombre, que tenga un lindo día.")
                break

            elif 'reproduce' in comando:
                busqueda = comando.replace('reproduce', '')
                hablar("Reproduciendo en YouTube " + busqueda)
                pywhatkit.playonyt(busqueda)
                hablar(f"¿En qué más puedo ayudarte señor, {nombre_usuario.capitalize()}?")

            elif 'hora' in comando:
                hora_actual = obtener_hora_actual()
                hablar(f"Claro, la hora actual es {hora_actual}")

            elif 'nuevo correo' in comando:
                 url = "https://mail.google.com/mail/u/0/?ogbl#inbox" # URL de Gmail
                 webbrowser.open(url)
                 hablar("Abriendo para redactar nuevo correo")

            elif 'correo' in comando:
                abrir_cuenta_google()
            else:
                hablar("No entendí tu petición. ¿Puedes repetirlo?")
    else:
        print("Jarvis está durmiendo...")