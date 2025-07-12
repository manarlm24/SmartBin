import cv2

import numpy as np

import tflite_runtime.interpreter as tflite

import RPi.GPIO as GPIO

import time

from time import sleep

import smtplib

from email.mime.multipart import MIMEMultipart

from email.mime.text import MIMEText



GPIO.setmode(GPIO.BOARD)

GPIO.setup(16, GPIO.OUT)  # Servo 1

GPIO.setup(18, GPIO.OUT)  # Servo 2



# Set up PWM for both servos

servo1 = GPIO.PWM(16, 50)

servo2 = GPIO.PWM(18, 50)

servo1.start(0)

servo2.start(0)



# Define GPIO pins for the first ultrasonic sensor

TRIG1 = 24

ECHO1 = 26



# Define GPIO pins for the second ultrasonic sensor

TRIG2 = 8

ECHO2 = 10



# Setup GPIO pins for the first sensor

GPIO.setup(TRIG1, GPIO.OUT)

GPIO.setup(ECHO1, GPIO.IN)



# Setup GPIO pins for the second sensor

GPIO.setup(TRIG2, GPIO.OUT)

GPIO.setup(ECHO2, GPIO.IN)



def measure_distance(trig, echo):

    # Set trigger to HIGH

    GPIO.output(trig, True)



    # Wait for a short duration

    time.sleep(0.00001)



    # Set trigger to LOW

    GPIO.output(trig, False)



    # Measure the time taken for the ultrasonic pulse to return

    pulse_start, pulse_end = 0, 0

    while GPIO.input(echo) == 0:

        pulse_start = time.time()



    while GPIO.input(echo) == 1:

        pulse_end = time.time()



    # Calculate distance

    pulse_duration = pulse_end - pulse_start

    distance = pulse_duration * 17150  # Speed of sound = 343 m/s, distance = time * speed



    # Round distance to 2 decimal places

    return round(distance, 2)



def controlServos(prediction, servo1, servo2, TRIG1, ECHO1, TRIG2, ECHO2):

    if (prediction == 0 and measure_distance(TRIG2, ECHO2) < 10) or (prediction == 3 and measure_distance(TRIG1, ECHO1) < 10):

        sendEmail(prediction)

    if prediction == 0 and measure_distance(TRIG2, ECHO2) > 10:

        servo1.ChangeDutyCycle(7.5)

        sleep(3)

        servo1.ChangeDutyCycle(2.5)

    elif prediction == 3 and measure_distance(TRIG1, ECHO1) > 10:

        servo2.ChangeDutyCycle(6.5)

        sleep(3)

        servo2.ChangeDutyCycle(12)



def sendEmail(prediction):

    sender_email = 'senderraspberry87@gmail.com'

    sender_password = 'jqed ybib uonv mpxd'

    receiver_email = 'techhanane23@gmail.com'

    subject = 'Alerte de replissage'

    body = 'La poubelle du verre est pleine !' if prediction == 0 else 'La poubelle du plastic est pleine !'

    msg = MIMEMultipart()

    msg['From'] = sender_email

    msg['To'] = receiver_email

    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))



    try:

        server = smtplib.SMTP('smtp.gmail.com', 587)

        server.starttls()

        server.login(sender_email, sender_password)

        server.send_message(msg)

        server.quit()

        print("Email sent successfully!")

    except Exception as e:

        print(f"Failed to send email. Error: {e}")



def preprocess(frame):

    resized_frame = cv2.resize(frame, (224, 224))

    normalized_frame = resized_frame / 255.0

    return normalized_frame



interpreter = tflite.Interpreter(model_path="model.tflite")

interpreter.allocate_tensors()

input_details = interpreter.get_input_details()

output_details = interpreter.get_output_details()

class_labels = ["glass", "metal", "paper", "plastic"]



cap = cv2.VideoCapture(0)



while True:

    command = input("Enter 'c' to capture a frame or 'q' to quit: ").strip().lower()

    

    if command == 'q':

        break

    elif command != 'c':

        continue



    ret, frame = cap.read()

    if not ret:

        break



    processed_frame = preprocess(frame)

    input_data = np.expand_dims(processed_frame, axis=0).astype(input_details[0]['dtype'])

    interpreter.set_tensor(input_details[0]['index'], input_data)

    interpreter.invoke()

    output_data = interpreter.get_tensor(output_details[0]['index'])



    predicted_class = np.argmax(output_data)

    confidence = output_data[0][predicted_class]

    label = class_labels[predicted_class]



    # Print results to the console

    print(f'Predicted: {label}, Confidence: {confidence:.2f}')



    controlServos(predicted_class, servo1, servo2, TRIG1, ECHO1, TRIG2, ECHO2)



cap.release()

cv2.destroyAllWindows()

servo1.stop()

servo2.stop()

GPIO.cleanup()



