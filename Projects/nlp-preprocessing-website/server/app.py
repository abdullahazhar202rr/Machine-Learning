from flask import Flask, request, jsonify
from flask_cors import CORS
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk import pos_tag
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import pandas as pd
import string
import re

app = Flask(__name__)
CORS(app)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt_tab')

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

def preprocess_text(text, options):
    processed_text = text
    steps = []

    if options.get('lowercase'):
        processed_text = processed_text.lower()
        steps.append('Converted to lowercase')

    if options.get('remove_punctuation'):
        processed_text = processed_text.translate(str.maketrans('', '', string.punctuation))
        steps.append('Removed punctuation')

    if options.get('remove_numbers'):
        processed_text = re.sub(r'\d+', '', processed_text)
        steps.append('Removed numbers')

    tokens = word_tokenize(processed_text)

    if options.get('remove_stopwords'):
        stop_words = set(stopwords.words('english'))
        tokens = [word for word in tokens if word.lower() not in stop_words]
        steps.append('Removed stopwords')

    if options.get('stemming'):
        tokens = [stemmer.stem(word) for word in tokens]
        steps.append('Applied stemming')

    if options.get('lemmatization'):
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        steps.append('Applied lemmatization')

    processed_text = ' '.join(tokens)

    return {
        'original': text,
        'processed': processed_text,
        'tokens': tokens,
        'steps': steps
    }

@app.route('/api/preprocess', methods=['POST'])
def preprocess():
    data = request.json
    text = data.get('text', '')
    options = data.get('options', {})

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    result = preprocess_text(text, options)
    return jsonify(result)

@app.route('/api/pos_tag', methods=['POST'])
def pos_tagging():
    data = request.json
    text = data.get('text', '')
    options = data.get('options', {})

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    preprocessed = preprocess_text(text, options)
    tokens = preprocessed['tokens']

    pos_tags = pos_tag(tokens)

    pos_explanation = {
        'NN': 'Noun, singular',
        'NNS': 'Noun, plural',
        'NNP': 'Proper noun, singular',
        'NNPS': 'Proper noun, plural',
        'VB': 'Verb, base form',
        'VBD': 'Verb, past tense',
        'VBG': 'Verb, gerund/present participle',
        'VBN': 'Verb, past participle',
        'VBP': 'Verb, present tense',
        'VBZ': 'Verb, 3rd person singular present',
        'JJ': 'Adjective',
        'JJR': 'Adjective, comparative',
        'JJS': 'Adjective, superlative',
        'RB': 'Adverb',
        'RBR': 'Adverb, comparative',
        'RBS': 'Adverb, superlative',
        'DT': 'Determiner',
        'IN': 'Preposition/subordinating conjunction',
        'CC': 'Coordinating conjunction',
        'PRP': 'Personal pronoun',
        'PRP$': 'Possessive pronoun',
        'TO': 'to',
        'MD': 'Modal',
        'CD': 'Cardinal number',
    }

    tagged_with_explanation = [
        {
            'word': word,
            'tag': tag,
            'explanation': pos_explanation.get(tag, 'Other')
        }
        for word, tag in pos_tags
    ]

    # return jsonify({
    #     'original': text,
    #     'preprocessed': preprocessed['processed'],
    #     'steps': preprocessed['steps'],
    #     'pos_tags': tagged_with_explanation
    # }
    return jsonify({
    'original': text,
    'preprocessed': preprocessed['processed'],
    'tokens': preprocessed['tokens'],  # 👈 This line fixes the error
    'steps': preprocessed['steps'],
    'pos_tags': tagged_with_explanation
})


    

@app.route('/api/bag_of_words', methods=['POST'])
def bag_of_words():
    data = request.json
    texts = data.get('texts', [])

    if not texts or len(texts) == 0:
        return jsonify({'error': 'No texts provided'}), 400

    texts = [str(t) for t in texts if t and str(t).strip()]

    if len(texts) == 0:
        return jsonify({'error': 'No valid texts provided'}), 400

    try:
        vectorizer = CountVectorizer()
        bow_matrix = vectorizer.fit_transform(texts)

        feature_names = vectorizer.get_feature_names_out()
        bow_array = bow_matrix.toarray()

        df = pd.DataFrame(bow_array, columns=feature_names)
        df.insert(0, 'Document', [f'Doc {i+1}' for i in range(len(texts))])

        vocab_df = pd.DataFrame({
            'Word': feature_names,
            'Index': range(len(feature_names))
        })

        # return jsonify({
        #     'bow_dataframe': df.to_dict('records'),
        #     'bow_columns': list(df.columns),
        #     'vocabulary_dataframe': vocab_df.to_dict('records'),
        #     'vocabulary_columns': list(vocab_df.columns),
        #     'vocabulary_size': len(feature_names),
        #     'original_texts': texts
        # })
        return jsonify({
    'bow_dataframe': df.to_dict('records'),
    'bow_columns': list(df.columns),
    'vocabulary_dataframe': vocab_df.to_dict('records'),
    'vocabulary_columns': list(vocab_df.columns),
    'vocabulary_size': len(feature_names),
    'original_texts': texts,
    'steps': [],         # 👈 Add this
    'tokens': []         # 👈 Add this
})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tfidf', methods=['POST'])
def tfidf():
    data = request.json
    texts = data.get('texts', [])

    if not texts or len(texts) == 0:
        return jsonify({'error': 'No texts provided'}), 400

    texts = [str(t) for t in texts if t and str(t).strip()]

    if len(texts) == 0:
        return jsonify({'error': 'No valid texts provided'}), 400

    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)

        feature_names = vectorizer.get_feature_names_out()
        tfidf_array = tfidf_matrix.toarray()

        df = pd.DataFrame(tfidf_array, columns=feature_names)
        df.insert(0, 'Document', [f'Doc {i+1}' for i in range(len(texts))])

        for col in df.columns:
            if col != 'Document':
                df[col] = df[col].round(4)

        vocab_df = pd.DataFrame({
            'Word': feature_names,
            'Index': range(len(feature_names))
        })

        # return jsonify({
        #     'tfidf_dataframe': df.to_dict('records'),
        #     'tfidf_columns': list(df.columns),
        #     'vocabulary_dataframe': vocab_df.to_dict('records'),
        #     'vocabulary_columns': list(vocab_df.columns),
        #     'vocabulary_size': len(feature_names),
        #     'original_texts': texts
        # })
        return jsonify({
    'tfidf_dataframe': df.to_dict('records'),
    'tfidf_columns': list(df.columns),
    'vocabulary_dataframe': vocab_df.to_dict('records'),
    'vocabulary_columns': list(vocab_df.columns),
    'vocabulary_size': len(feature_names),
    'original_texts': texts,
    'steps': [],         # 👈 Add this
    'tokens': []         # 👈 Add this
})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
