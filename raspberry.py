import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import threading

TRIG_PIN = 23
ECHO_PIN = 24
GREEN_LED = 22
RED_LED = 27
DISTANCE_THRESHOLD = 40
TIMEOUT = 30

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)

MQTT_BROKER = "192.168.0.243"
MQTT_PORT = 1883
MQTT_TOPIC = "esteira/status"
MQTT_TOPIC_RESTART = "esteira/reiniciar"

client = mqtt.Client()
reiniciar_event = threading.Event()

def on_connect(client, userdata, flags, rc):
  print("Conectado com código de resultado: " + str(rc))
  client.subscribe(MQTT_TOPIC_RESTART)
  client.publish(MQTT_TOPIC, "funcionando", qos=1)

client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def medir_distancia():
  GPIO.output(TRIG_PIN, True)
  time.sleep(0.00001)
  GPIO.output(TRIG_PIN, False)
  
  while GPIO.input(ECHO_PIN) == 0:
    inicio_pulso = time.time()
  
  while GPIO.input(ECHO_PIN) == 1:
    fim_pulso = time.time()
  
  duracao = fim_pulso - inicio_pulso
  distancia = (duracao * 34300) / 2
  return distancia

def monitorar_esteira():
  ultimo_tempo_objeto = time.time()
  detectando = True
  espera_reiniciar = True
  tempo_inicio = time.time()

  try:
    while True:
      if reiniciar_event.is_set():
        detectando = True
        GPIO.output(GREEN_LED, GPIO.HIGH)
        GPIO.output(RED_LED, GPIO.LOW)
        reiniciar_event.clear()
        espera_reiniciar = True
        tempo_inicio = time.time()

      if espera_reiniciar:
        print("Esperando detecção inicial...")
        distancia = medir_distancia()
        if distancia < DISTANCE_THRESHOLD:
          espera_reiniciar = False

        if time.time() - tempo_inicio > TIMEOUT:
          print("Esteira parada (timeout na detecção inicial)")
          GPIO.output(GREEN_LED, GPIO.LOW)
          GPIO.output(RED_LED, GPIO.HIGH)
          client.publish(MQTT_TOPIC, "parada", qos=1)
          detectando = False
          espera_reiniciar = False
          continue

        time.sleep(1)
        continue

      if not detectando:
        GPIO.output(GREEN_LED, GPIO.LOW)
        GPIO.output(RED_LED, GPIO.HIGH)
        time.sleep(1)
        continue

      distancia = medir_distancia()

      if distancia < DISTANCE_THRESHOLD:
        print("Produto detectado")
        GPIO.output(GREEN_LED, GPIO.HIGH)
        GPIO.output(RED_LED, GPIO.LOW)
        client.publish(MQTT_TOPIC, "funcionando", qos=1)
        ultimo_tempo_objeto = time.time()
        espera_reiniciar = False
      else:
        if time.time() - ultimo_tempo_objeto > TIMEOUT:
          print("Esteira parada")
          GPIO.output(GREEN_LED, GPIO.LOW)
          GPIO.output(RED_LED, GPIO.HIGH)
          client.publish(MQTT_TOPIC, "parada", qos=1)
          detectando = False

      time.sleep(1)
  
  except KeyboardInterrupt:
    print("Monitoramento encerrado")
  finally:
    GPIO.cleanup()

def on_message(client, userdata, msg):
  global detectando, ultimo_tempo_objeto
  if msg.topic == MQTT_TOPIC_RESTART and msg.payload.decode() == "reiniciar":
    print("Reiniciando a esteira...")
    detectando = True
    ultimo_tempo_objeto = time.time()
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)
    client.publish(MQTT_TOPIC, "reiniciando", qos=1)
    reiniciar_event.set()
    print("Esteira reiniciada e pronta para detecção.")
    client.publish(MQTT_TOPIC, "funcionando", qos=1)

client.on_message = on_message
client.loop_start()

monitorar_esteira()
