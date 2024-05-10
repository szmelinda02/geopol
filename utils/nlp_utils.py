from transformers import AutoTokenizer, BertForTokenClassification, pipeline
import syntok.segmenter as segmenter
import spacy
from newspaper import Article


class NLPClass:
    def __init__(self):
        #for NER
        NER_MODEL_NAME = 'en_core_web_trf'
        self.ner = spacy.load(NER_MODEL_NAME)
        # for sentiment
        SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.sentiment_scorer = pipeline(task="sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        
        
    def return_ner_labels(self, text):
        doc = self.ner(text)
        return [(ent.text, ent.label_) for ent in doc.ents]


    def get_named_entities(self, text, title=None):
        
        ner_result = self.ner(text)
        """Visualize NER with the help of SpaCy"""
        ents = []
        for ent in ner_result:
            e = {}
            # Add the start and end positions of the entity
            e["start"] = ent["start"]
            e["end"] = ent["end"]
            # Add the score if you want in the label
            # e["label"] = f"{ent["entity"]}-{ent['score']:.2f}"
            e["label"] = ent["entity_group"]
            if ents and -1 <= ent["start"] - ents[-1]["end"] <= 1 and ents[-1]["label"] == e["label"]:
                # If the current entity is shared with the previous entity,
                # simply extend the entity end position instead of adding a new one
                ents[-1]["end"] = e["end"]
                continue
            ents.append(e)
        # Construct data required for displacy.render() method
        render_data = [
            {
                "text": text,
                "ents": ents,
                "title": title,
            }
        ]
        return render_data

    def split_text(self, text):
        if text is None:
            return None
        paragraphs = []
        for paragraph in segmenter.analyze(text):
            sentences = []
            for sentence in paragraph:
                tokens = [token.spacing + token.value for token in sentence]
                sentences.append(''.join(tokens))
            paragraphs.append(' '.join(sentences))
        return paragraphs
    
    def get_article_infos(self,url):
        try:
            article = Article(url)
            article.download()
            article.html
            article.parse()
            return article
        except:
            return None