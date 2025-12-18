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
from flask_sqlalchemy import SQLAlchemy
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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }

# Global Vector Store (In-memory for demo)
# Global Vector Store (In-memory for demo, but we will try to load from disk)
vector_store = None
FAISS_INDEX_PATH = "faiss_index"

def load_vector_store():
    global vector_store
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            embeddings = OpenAIEmbeddings()
            vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            print("Loaded FAISS index from disk.")
        except Exception as e:
            print(f"Failed to load FAISS index: {e}")
            vector_store = None

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')




@app.route('/api/upload', methods=['POST'])
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
            
            # Save to disk
            vector_store.save_local(FAISS_INDEX_PATH)
                
            return jsonify({'message': f'Successfully processed {filename}', 'chunks': len(splits)})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    global vector_store
    """Handle chat requests"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        session_id = request.headers.get('X-Session-ID', 'default')

        # Save User Message
        user_msg_db = ChatMessage(session_id=session_id, role='user', content=user_message)
        db.session.add(user_msg_db)
        db.session.commit()
        
        # Initialize the model
        try:
            llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
            
            source_docs = []
            chain = None
            inputs = {}
            
            if vector_store:
                # RAG Flow with LCEL
                retriever = vector_store.as_retriever()
                
                # Retrieve and format documents
                docs = retriever.invoke(user_message)
                formatted_context = "\n\n".join(doc.page_content for doc in docs)
                
                # Extract sources
                source_docs = [doc.metadata.get("source", "Unknown") for doc in docs]
                source_docs = list(set(source_docs))
                
                prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}""")
                
                # LCEL Chain
                chain = prompt | llm | StrOutputParser()
                inputs = {"context": formatted_context, "input": user_message}
                
            else:
                # Standard Chat Flow
                prompt = ChatPromptTemplate.from_template("{input}")
                chain = prompt | llm | StrOutputParser()
                inputs = {"input": user_message}
            
            def generate():
                full_response = ""
                for chunk in chain.stream(inputs):
                    full_response += chunk
                    yield chunk
                
                # Save Assistant Message
                with app.app_context():
                    ai_msg_db = ChatMessage(session_id=session_id, role='assistant', content=full_response)
                    db.session.add(ai_msg_db)
                    db.session.commit()

            response = Response(stream_with_context(generate()), content_type='text/plain')
            response.headers['X-Sources'] = json.dumps(source_docs)
            return response

        except Exception as e:
            return jsonify({'error': f"LangChain Error: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent', methods=['POST'])
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

@app.route('/api/history', methods=['GET'])
def get_history():
    session_id = request.headers.get('X-Session-ID', 'default')
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    return jsonify([msg.to_dict() for msg in messages])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_vector_store()
    app.run(debug=True, host='0.0.0.0', port=5000)