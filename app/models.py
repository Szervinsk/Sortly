from app import db
from datetime import datetime

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_snippet = db.Column(db.String(100)) # Um resumo do email (primeiros chars)
    full_text = db.Column(db.Text)              # O texto completo original
    category = db.Column(db.String(50))         # Produtivo / Improdutivo
    ai_response = db.Column(db.Text)            # A resposta gerada
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Data automática

    def to_dict(self):
        return {
            "id": self.id,
            "snippet": self.subject_snippet,
            "category": self.category,
            "date": self.created_at.strftime("%d/%m/%Y %H:%M")
        }