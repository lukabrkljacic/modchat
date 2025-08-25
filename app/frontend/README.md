# LLM Chat Interface - Frontend

A modern, responsive web application that provides an intuitive user interface for the LLM Chat Interface backend. This frontend features a sophisticated component-based chat interface with advanced settings and real-time AI interactions.

## 🚀 Features

### **Component-Based Chat Interface**
- **4-Column Layout**: User Prompt, AI Response, Component Breakdown, Final Output
- **Real-time Component Editing**: Click-to-edit individual response components
- **Structured Output Generation**: Email, report, and document formatting
- **Copy-to-Clipboard**: One-click copying of generated content

### **Advanced Configuration Panel**
- **Sliding Settings Sidebar**: Collapsible advanced settings panel
- **System Prompt Editor**: Custom AI behavior configuration
- **Model Selection**: Multi-vendor AI model selection (OpenAI, Anthropic)
- **Response Format Controls**: JSON structure definitions
- **Parameter Sliders**: Temperature, max tokens, and other model settings

### **Modern UI/UX**
- **Dark Theme**: Eye-friendly dark interface
- **Responsive Design**: Mobile-first design with tablet and desktop optimization
- **Font Awesome Icons**: Professional iconography throughout
- **Smooth Animations**: CSS transitions and hover effects
- **Accessibility**: Proper contrast ratios and semantic markup

### **File Upload Support**
- **Drag & Drop**: Intuitive file upload interface
- **Multiple Formats**: PDF, DOCX, CSV, TXT, and more
- **File Processing Feedback**: Real-time upload status

## 📁 Project Structure

```
servers/frontend/
├── src/
│   ├── app.py                  # Flask application server
│   ├── templates/
│   │   └── index.html         # Main application template
│   └── static/
│       ├── css/
│       │   ├── style.css      # Custom application styles
│       │   └── all.min.css    # Font Awesome icons
│       └── js/
│           └── main.js        # Frontend JavaScript logic
├── requirements.txt           # Python dependencies
├── Dockerfile                # Container configuration
└── README.md                 # This documentation
```

## 🛠️ Installation & Setup

### **Local Development**

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd servers/frontend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   # Create .env file (optional)
   touch .env
   ```

   Available environment variables:
   ```env
   FLASK_DEBUG=True
   FLASK_HOST=0.0.0.0
   FLASK_PORT=8080
   BACKEND_BASE_URL=http://localhost:5000
   BACKEND_EXTERNAL_BASE_URL=http://localhost:5000
   MODEL_LISTING_ENDPOINT=models
   ```

5. **Start the development server:**
   ```bash
   python src/app.py
   ```

6. **Access the application:**
   ```
   http://localhost:8080
   ```

### **Docker Deployment**

#### **Development Container**
```bash
# Build development image
docker build --target dev -t llm-frontend:dev .

# Run development container
docker run -it -p 8080:8000 \
  -e BACKEND_BASE_URL=http://backend:5000 \
  -v $(pwd)/src:/src \
  --name llm-frontend-dev \
  llm-frontend:dev
```

#### **Production Container**
```bash
# Build production image
docker build --target prod -t llm-frontend:prod .

# Run production container
docker run -d -p 8080:8000 \
  -e BACKEND_EXTERNAL_BASE_URL=http://your-backend-domain.com \
  --name llm-frontend-prod \
  llm-frontend:prod
```

## 🔧 Configuration

### **Backend Integration**

The frontend communicates with the backend API through configurable endpoints:

```javascript
// Set in templates/index.html
window.BACKEND_URL = "{{BACKEND_URL}}";
```

**Environment Variables:**
- `BACKEND_BASE_URL`: Internal backend URL (for server-side requests)
- `BACKEND_EXTERNAL_BASE_URL`: External backend URL (for client-side requests)

### **Model Configuration**

Models are dynamically loaded from the backend `/models` endpoint. The interface supports:

- **OpenAI Models**: GPT-4, GPT-4.1 variants
- **Anthropic Models**: Claude 3 family
- **Vendor Extensions**: Easy addition of new AI providers

## 🎨 UI Components

### **Chat Interface**

**4-Column Layout:**
1. **User Prompt** - Input message display
2. **AI Response** - Complete AI response
3. **Component Breakdown** - Editable response components
4. **Final Output** - Formatted final result

**Interactive Features:**
- Click-to-edit components
- Real-time formatting
- Copy-to-clipboard functionality
- Component reordering

### **Settings Sidebar**

**System Prompt Editor:**
- Multi-line text editor
- Syntax highlighting
- Save/restore functionality

**Model Parameters:**
- Temperature slider (0.0 - 1.0)
- Max tokens input
- Top-p/Top-k controls
- Custom parameter support

**Response Format:**
- JSON schema editor
- Predefined templates
- Custom format definitions

### **File Upload**

**Supported Formats:**
- Text files (`.txt`)
- PDF documents (`.pdf`)
- Word documents (`.docx`)
- Excel files (`.xlsx`, `.csv`)
- Other formats as configured

## 📱 Responsive Design

### **Desktop (≥1200px)**
- Full 4-column layout
- Sidebar always visible
- Maximum feature density

### **Tablet (768px - 1199px)**
- Collapsed sidebar by default
- 3-column chat layout
- Touch-optimized controls

### **Mobile (≤767px)**
- Single-column stacked layout
- Slide-out sidebar menu
- Mobile-first interactions

## 🔌 API Integration

### **Frontend API Calls**

```javascript
// Chat request
fetch(`${window.BACKEND_URL}/chat`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: userInput,
        model: selectedModel,
        vendor: selectedVendor,
        settings: advancedSettings,
        decompose: true
    })
});

// File upload
const formData = new FormData();
formData.append('file', file);
fetch(`${window.BACKEND_URL}/upload`, {
    method: 'POST',
    body: formData
});
```

### **Error Handling**

The frontend includes comprehensive error handling:
- Network connectivity issues
- Backend API errors
- File upload failures
- Model initialization errors

## 🎯 Key Features Deep Dive

### **Component Decomposition**

When decomposition is enabled, AI responses are broken into logical components:

```javascript
// Example decomposed response
{
  "components": [
    {
      "type": "greeting",
      "content": "Hello! I hope you're doing well.",
      "title": "Greeting"
    },
    {
      "type": "body",
      "content": "I wanted to discuss the project updates...",
      "title": "Main Content"
    },
    {
      "type": "closing",
      "content": "Best regards,",
      "title": "Closing"
    }
  ]
}
```

### **Real-time Editing**

Users can edit any component in real-time:
- Click edit icon on any component
- Inline editing with auto-save
- Immediate final output regeneration
- Undo/redo functionality

### **Format Templates**

Built-in templates for common outputs:
- **Email**: Subject, greeting, body, closing
- **Report**: Title, summary, findings, recommendations
- **Document**: Custom sections based on content

## 🚦 Health Monitoring

The frontend includes health check endpoints:

```bash
# Health check
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "ok"
}
```

## 🔒 Security Considerations

- **CORS Configuration**: Proper cross-origin request handling
- **Input Sanitization**: XSS prevention on user inputs
- **File Upload Security**: Type validation and size limits
- **API Key Protection**: No API keys exposed to client-side

## 🐛 Troubleshooting

### **Common Issues**

**Backend Connection Failed:**
```bash
# Check backend URL configuration
echo $BACKEND_EXTERNAL_BASE_URL

# Verify backend is running
curl http://localhost:5000/health
```

**Models Not Loading:**
```bash
# Check models endpoint
curl http://localhost:5000/models
```

**File Upload Issues:**
- Verify file size limits
- Check supported file types
- Ensure backend storage permissions

### **Development Debugging**

Enable debug mode:
```bash
export FLASK_DEBUG=True
python src/app.py
```

Browser console logging:
```javascript
// Enable verbose logging
window.DEBUG = true;
```

## 🔄 Development Workflow

### **Hot Reloading**

For development, the frontend supports hot reloading:
```bash
# With file watching
python src/app.py --reload
```

### **Static Asset Development**

CSS and JavaScript changes are reflected immediately in development mode.

### **Testing**

```bash
# Run frontend tests
pytest tests/

# Test with backend integration
python -m pytest tests/integration/
```

## 📋 Dependencies

### **Python Dependencies**
- `flask` - Web framework
- `python-dotenv` - Environment variable management
- `requests` - HTTP client for backend communication
- `gunicorn` - Production WSGI server

### **Frontend Dependencies**
- **Font Awesome 6.0** - Icon library
- **Custom CSS Grid** - Layout system
- **Vanilla JavaScript** - No framework dependencies

## 🚀 Performance Optimization

### **Asset Optimization**
- Minified CSS and JavaScript
- Font Awesome subset loading
- Lazy loading for non-critical components

### **Network Optimization**
- Request debouncing for user input
- Efficient WebSocket connections (future)
- Caching for static assets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style
4. Add tests for new features
5. Submit a pull request

### **Code Style**
- Python: Follow PEP 8
- JavaScript: ES6+ standards
- CSS: BEM methodology
- HTML: Semantic markup

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## 🔗 Related Documentation

- [Backend API Documentation](../backend/README.md)
- [Deployment Guide](../docs/deployment.md)
- [Architecture Overview](../docs/architecture.md)