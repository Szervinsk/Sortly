import os
import re
import json
import PyPDF2
from flask import render_template, request, jsonify
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types
from app import app, db 
from app.models import EmailLog

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Funções Auxiliares de Texto ---
def preprocess_text(text):
    text = re.sub(r'[^\w\s.,!?@]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text_from_file(filepath, extension):
    text = ""
    try:
        if extension == 'pdf':
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extract = page.extract_text()
                    if extract: text += extract + "\n"
        elif extension == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        return None
    return text

# --- Função de Análise com IA ---
def analyze_with_ai(email_content, user_api_key=None):
    
    # 1. Prioriza a chave do usuário (se existir), senão usa a do servidor (.env)
    api_key_to_use = user_api_key if user_api_key else os.getenv("GOOGLE_API_KEY")

    if not api_key_to_use:
        return {"categoria": "Erro", "resposta_sugerida": "Nenhuma chave de API configurada."}

    # Inicializa o cliente
    client = genai.Client(api_key=api_key_to_use)

    prompt = f"""
    Você é um assistente de triagem de emails.
    Tarefa:
    1. Analise o conteúdo do email abaixo.
    2. Classifique-o estritamente como "Produtivo" (requer ação/suporte) ou "Improdutivo" (agradecimentos, spam, sem ação necessária).
    3. Escreva uma sugestão de resposta educada e profissional baseada na categoria.

    Email para análise:
    "{email_content}"

    Retorne APENAS um JSON com as chaves "categoria" e "resposta_sugerida".
    """
    
    try:
        # Usando 'gemini-1.5-flash' para maior estabilidade no plano gratuito
        # Se você tiver acesso pago, pode tentar mudar para 'gemini-2.0-flash'
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        return json.loads(response.text)

    except Exception as e:
        print(f"Erro Gemini: {e}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return {
                "categoria": "Cota Excedida",
                "resposta_sugerida": "A chave utilizada atingiu o limite gratuito do Google. Tente outra chave nas Configurações ou aguarde alguns instantes."
            }
        return {"categoria": "Erro", "resposta_sugerida": str(e)}

# --- Rotas da Aplicação ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preferences')
def preferences():
    return render_template('preferences.html')

@app.route('/history')
def history():
    # Busca emails ordenados do mais recente para o mais antigo
    try:
        logs = EmailLog.query.order_by(EmailLog.created_at.desc()).all()
    except Exception:
        logs = []
    return render_template('history.html', logs=logs)

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Recupera chave do cabeçalho (enviada pelo JS se estiver salva)
    user_key = request.headers.get('X-Gemini-Key')

    email_text = ""

    # 2. Lógica para Processar Arquivo (PDF/TXT)
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            ext = filename.rsplit('.', 1)[1].lower()
            email_text = extract_text_from_file(filepath, ext)
            
            # Remove o arquivo temporário após a leitura
            try:
                os.remove(filepath)
            except:
                pass

    # 3. Lógica para Processar Texto Colado
    elif 'email_text' in request.form and request.form['email_text'].strip() != '':
        email_text = request.form['email_text']
    
    # Validação se algo foi recebido
    if not email_text:
        return jsonify({"error": "Nenhum conteúdo de texto ou arquivo válido recebido."}), 400

    # 4. Pré-processamento e Análise
    clean_text = preprocess_text(email_text)
    
    # Chama a IA passando a chave do usuário (se houver)
    result = analyze_with_ai(clean_text, user_api_key=user_key)
    
    # 5. Salvar no Banco de Dados (apenas se a análise foi bem sucedida)
    if result.get("categoria") != "Erro" and result.get("categoria") != "Cota Excedida":
        try:
            # Cria um resumo (snippet) para a tabela
            snippet = (email_text[:70] + '...') if len(email_text) > 70 else email_text
            
            new_log = EmailLog(
                subject_snippet=snippet,
                full_text=email_text,
                category=result.get("categoria", "Desconhecido"),
                ai_response=result.get("resposta_sugerida", "")
            )
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
            # Não paramos o retorno ao usuário se o banco falhar, apenas logamos o erro no console.

    return jsonify(result)