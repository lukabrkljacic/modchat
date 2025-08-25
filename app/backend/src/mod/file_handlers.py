# file_handlers.py
"""
File handling utilities for the Flask LLM Chat application.
This module provides functions for processing uploaded files.
"""

import os
import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple
import mimetypes
from werkzeug.utils import secure_filename

# Langchain imports
try:
    from langchain.document_loaders import TextLoader, CSVLoader, PyPDFLoader, UnstructuredFileLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError as e:
    raise ImportError(f"Error importing Langchain modules: {str(e)}")

# Import custom error classes
from mod.errors.error_handlers import FileProcessingError

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_COMBINED_CONTENT = 100 * 1024  # 100KB - to avoid token limit issues
SUPPORTED_EXTENSIONS = {
    'txt': 'text/plain',
    'csv': 'text/csv',
    'pdf': 'application/pdf',
    'md': 'text/markdown',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'json': 'application/json',
    'html': 'text/html'
}

# File extension to loader mapping
FILE_LOADERS = {
    'txt': TextLoader,
    'csv': CSVLoader,
    'pdf': PyPDFLoader,
    'md': TextLoader,
    # Add more specific loaders as needed
    
    # Default loader for fallback
    'default': UnstructuredFileLoader
}

def validate_file(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a file to ensure it's safe to process.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if file exists
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large ({file_size} bytes). Maximum size is {MAX_FILE_SIZE} bytes."
    
    # Check file extension
    ext = filepath.split('.')[-1].lower() if '.' in filepath else None
    if not ext or ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {ext or 'unknown'}"
    
    # Check mime type (additional security)
    mime_type, _ = mimetypes.guess_type(filepath)
    expected_mime = SUPPORTED_EXTENSIONS.get(ext)
    if mime_type and expected_mime and mime_type != expected_mime:
        logger.warning(f"Mime type mismatch: {mime_type} != {expected_mime} for {filepath}")
        # Not returning False here as mime detection isn't always reliable
    
    return True, None

def get_loader_for_file(filepath: str) -> Any:
    """
    Gets the appropriate document loader for a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        An instantiated document loader
    
    Raises:
        FileProcessingError: If no appropriate loader is found
    """
    ext = filepath.split('.')[-1].lower() if '.' in filepath else None
    
    if not ext:
        raise FileProcessingError(f"Cannot determine file type for {filepath}")
    
    loader_class = FILE_LOADERS.get(ext, FILE_LOADERS.get('default'))
    
    if not loader_class:
        raise FileProcessingError(f"No document loader available for file type: {ext}")
    
    try:
        return loader_class(filepath)
    except Exception as e:
        logger.error(f"Error creating loader for {filepath}: {str(e)}")
        raise FileProcessingError(f"Failed to initialize document loader: {str(e)}")

def process_uploaded_files(file_paths: List[str], 
                           chunk_size: int = 1000, 
                           chunk_overlap: int = 100) -> Tuple[List[Any], List[Dict[str, str]]]:
    """
    Process uploaded files and convert them to documents for context.
    
    Args:
        file_paths: List of paths to uploaded files
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        
    Returns:
        Tuple of (processed_documents, failed_files)
        
    Raises:
        FileProcessingError: If all files fail to process
    """
    if not file_paths:
        return [], []
        
    logger.info(f"Processing {len(file_paths)} files")
    documents = []
    failed_files = []
    
    for file_path in file_paths:
        try:
            # Validate file
            is_valid, error_message = validate_file(file_path)
            if not is_valid:
                logger.warning(f"File validation failed: {error_message}")
                failed_files.append({"path": file_path, "error": error_message})
                continue
                
            # Get appropriate loader
            loader = get_loader_for_file(file_path)
            
            # Load the document
            logger.info(f"Loading file: {file_path}")
            loaded_docs = loader.load()
            
            # Add loaded documents to our collection
            documents.extend(loaded_docs)
            logger.info(f"Successfully loaded {len(loaded_docs)} documents from {file_path}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error loading file {file_path}: {error_msg}")
            logger.error(traceback.format_exc())
            failed_files.append({"path": file_path, "error": error_msg})
    
    # If we have documents, split them into chunks
    if documents:
        try:
            logger.info(f"Splitting {len(documents)} documents with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            split_docs = text_splitter.split_documents(documents)
            logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
            return split_docs, failed_files
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            logger.error(traceback.format_exc())
            failed_files.append({"path": "document_splitting", "error": str(e)})
            
            # Return the original unsplit documents if splitting fails
            return documents, failed_files
    
    # If all files failed
    if failed_files and not documents:
        error_messages = ", ".join([f"{f['path']}: {f['error']}" for f in failed_files])
        raise FileProcessingError(f"Failed to process all files: {error_messages}")
    
    return documents, failed_files

def extract_document_content(documents: List[Any], max_length: int = 8000) -> str:
    """
    Extract content from documents with length limit to avoid context overflow.
    
    Args:
        documents: List of processed document objects
        max_length: Maximum content length to return
        
    Returns:
        Extracted content as a string
    """
    if not documents:
        return ""
    
    try:
        # Extract content from each document with error handling
        contents = []
        for doc in documents:
            try:
                if hasattr(doc, 'page_content'):
                    contents.append(doc.page_content)
                else:
                    logger.warning(f"Document lacks page_content attribute: {type(doc)}")
                    # Try to convert to string as fallback
                    contents.append(str(doc))
            except Exception as e:
                logger.warning(f"Error extracting content from document: {str(e)}")
        
        # Combine content with separators
        combined = "\n\n".join(contents)
        
        # Trim if necessary to avoid exceeding context limits
        if len(combined) > max_length:
            logger.warning(f"Document content exceeded max length: {len(combined)} > {max_length}")
            combined = combined[:max_length] + "...(content truncated due to length)"
        
        return combined
    except Exception as e:
        logger.error(f"Error extracting document content: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a partial result if possible
        return "\n\n".join([getattr(doc, 'page_content', str(doc))[:100] for doc in documents]) + "...(error during content extraction)"

def get_supported_file_types() -> List[str]:
    """
    Returns a list of supported file extensions.
    
    Returns:
        List of file extensions (without the dot)
    """
    return list(SUPPORTED_EXTENSIONS.keys())

def cleanup_files(file_paths: List[str]) -> None:
    """
    Safely removes temporary files after processing.
    
    Args:
        file_paths: List of file paths to clean up
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")