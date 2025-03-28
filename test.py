import joblib
import numpy as np
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflow as tf
import re

# Load model and utilities
model = tf.keras.models.load_model("model/biLSTM.keras")
tokenizer = joblib.load("model/tokenizer.joblib")
label_encoder = joblib.load("model/label_encoder.joblib")

# Initialize NLP tools
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english")) - {"not", "no", "never"}

# Parameters
max_len = 100
confidence_threshold = 0.3

def preprocess_text(text):
    """Preprocess text: keep punctuation and perform lemmatization."""
    words = re.findall(r"[\w']+|[.,!?;]", text)
    words = [lemmatizer.lemmatize(word) for word in words if word.lower() not in stop_words]
    return " ".join(words)

def predict_emotion(sentence):
    """Predict emotion of a given sentence."""
    processed_sentence = preprocess_text(sentence)
    sequence = tokenizer.texts_to_sequences([processed_sentence])
    padded_sequence = pad_sequences(sequence, maxlen=max_len, padding="post")
    prediction = model.predict(padded_sequence)[0]

    max_prob = np.max(prediction)
    predicted_label = np.argmax(prediction)
    predicted_emotion = label_encoder.inverse_transform([predicted_label])[0]

    return predicted_emotion if max_prob >= confidence_threshold else "Neutral", prediction


def split_sentences(text):
    # Improved regex to handle newlines, multiple spaces, and punctuation without space
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!|\n)\s+', text)


def analyze_journal(journal):
    """Analyze journal entry for sentence-level and overall emotion detection."""
    sentences = split_sentences(journal)
    sentence_emotions = []
    emotion_scores = np.zeros(len(label_encoder.classes_))

    for sentence in sentences:
        if not sentence.strip():  # Skip empty sentences
            continue
        emotion, probabilities = predict_emotion(sentence)

        if emotion != "Neutral":
            sentence_emotions.append((sentence, emotion))
            emotion_scores += probabilities
        #sentence_emotions.append((sentence, emotion))
        #emotion_scores += probabilities


    # Hard Prediction (Most Frequent Emotion)
    emotion_counts = Counter(emotion for _, emotion in sentence_emotions)
    dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "Neutral"

    # Soft Prediction (Mean Probabilities)
    if np.sum(emotion_scores) == 0:
        soft_emotion = "Neutral"
    else:
        soft_emotion = label_encoder.inverse_transform([np.argmax(emotion_scores)])[0]

    return sentence_emotions, dominant_emotion, soft_emotion

if __name__ == '__main__':
    journal = input("Enter your journal entry: ")

    sentence_emotions, dominant_emotion, soft_emotion = analyze_journal(journal)

    print("\nSentence-wise Emotion Predictions:")
    for sentence, emotion in sentence_emotions:
        print(f"➡ {sentence}  →  {emotion}")

    print(f"\n🧠 Predicted Dominant Emotion (Hard): {dominant_emotion}")
    print(f"🧠 Predicted Dominant Emotion (Soft): {soft_emotion}")
