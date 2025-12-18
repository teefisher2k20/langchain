"""
LangChain Web Application
A modern web interface for demonstrating LangChain capabilities
"""
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
from flask_cors import CORS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain.chains import ConversationChain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import AgentExecutor, create_openai_functions_agent, tool
from langchain_core.prompts import MessagesPlaceholder
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import shutil

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure app
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Global Vector Store (In-memory for demo)
vector_store = None

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
@login_required
def index():
    """Main application page"""
    return render_template('index.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return jsonify({'message': 'Logged in successfully'})
        return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Registered successfully'})
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})


@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    global vector_store
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Load and process document
            if filename.endswith('.pdf'):
                loader = PyPDFLoader(filepath)
            else:
                loader = TextLoader(filepath)
                
            docs = loader.load()
            
            # Split text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)
            
            # Create/Update Vector Store
            embeddings = OpenAIEmbeddings()
            if vector_store is None:
                vector_store = FAISS.from_documents(splits, embeddings)
            else:
                vector_store.add_documents(splits)
                
            return jsonify({'message': f'Successfully processed {filename}', 'chunks': len(splits)})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    global vector_store
    """Handle chat requests"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Initialize the model
        try:
            llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
            
            ai_response = ""
            source_docs = []
            
            if vector_store:
                # RAG Flow with LCEL
                retriever = vector_store.as_retriever()
                
                # Retrieve and format documents
                docs = retriever.invoke(user_message)
                formatted_context = "\n\n".join(doc.page_content for doc in docs)
                
                prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}""")
                
                # LCEL Chain
                chain = prompt | llm | StrOutputParser()
                ai_response = chain.invoke({"context": formatted_context, "input": user_message})
                
                # Extract sources
                source_docs = [doc.metadata.get("source", "Unknown") for doc in docs]
                # Deduplicate sources
                source_docs = list(set(source_docs))
            else:
                # Standard Chat Flow
                msg = llm.invoke(user_message)
                ai_response = msg.content
            
            response_data = {
                'message': ai_response,
                'timestamp': datetime.now().isoformat(),
                'model': 'gpt-3.5-turbo',
                'sources': source_docs
            }
        except Exception as e:
            return jsonify({'error': f"LangChain Error: {str(e)}"}), 500
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent', methods=['POST'])
@login_required
def agent_run():
    """Handle agent requests"""
    try:
        data = request.get_json()
        user_goal = data.get('goal', '')
        
        if not user_goal:
            return jsonify({'error': 'No goal provided'}), 400
            
        try:
            llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
            
            # Define Tools
            search = DuckDuckGoSearchRun()
            
            @tool
            def calculator(expression: str) -> str:
                """Calculates a mathematical expression."""
                try:
                    return str(eval(expression, {"__builtins__": None}, {}))
                except Exception as e:
                    return f"Error: {e}"

            tools = [search, calculator]
            
            # Create Agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful AI assistant. Use the available tools to answer the user's question."),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_openai_functions_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            
            # Run Agent
            result = agent_executor.invoke({"input": user_goal})
            
            response = {
                'output': result['output'],
                'timestamp': datetime.now().isoformat(),
            }
            return jsonify(response)
            
        except Exception as e:
            return jsonify({'error': f"Agent Error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available LangChain models"""
    models = [
        {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'provider': 'OpenAI'},
        {'id': 'gpt-4', 'name': 'GPT-4', 'provider': 'OpenAI'},
        {'id': 'claude-3', 'name': 'Claude 3', 'provider': 'Anthropic'},
        {'id': 'llama-2', 'name': 'Llama 2', 'provider': 'Meta'},
    ]
    return jsonify(models)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'langchain_version': '0.3.15'
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)