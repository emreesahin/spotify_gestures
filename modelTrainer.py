import matplotlib.pyplot as plt
from mediapipe_model_maker import gesture_recognizer
import os
import tensorflow as tf
assert tf.__version__.startswith('2')

dataset_path = "/el_hareketleri_klasoru/"

print(dataset_path)
labels = []
for i in os.listdir(dataset_path):
    if os.path.isdir(os.path.join(dataset_path, i)):
        labels.append(i)
print(labels)
