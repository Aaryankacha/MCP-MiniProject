import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("LocalFileMCP", log_level="ERROR")

# Define where our real documents live
# This looks for a folder named "documents" in the same directory as this script
DOCS_DIR = Path(__file__).parent / "documents"

# Ensure the directory exists
if not DOCS_DIR.exists():
    DOCS_DIR.mkdir()

def _get_path(doc_id: str) -> Path:
    """Helper to safely get the file path."""
    # Security check: prevent users from accessing files outside DOCS_DIR
    safe_path = (DOCS_DIR / doc_id).resolve()
    if not str(safe_path).startswith(str(DOCS_DIR.resolve())):
        raise ValueError("Access denied: Cannot access files outside 'documents' folder")
    return safe_path

@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Read the contents of a real file from the documents folder."""
    file_path = _get_path(doc_id)
    
    if not file_path.exists():
        raise ValueError(f"Document {doc_id} not found")
        
    # Read text from the file
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "[Binary file or non-text content]"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def edit_doc(doc_id: str, content: str) -> str:
    """Edit (or create) a file in the documents folder."""
    file_path = _get_path(doc_id)
    
    try:
        file_path.write_text(content, encoding="utf-8")
        return f"Successfully saved {doc_id}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.resource("docs://documents")
def list_documents() -> list[str]:
    """List all filenames in the documents folder."""
    if not DOCS_DIR.exists():
        return []
    # Return a list of filenames (e.g., ["notes.txt", "readme.md"])
    return [f.name for f in DOCS_DIR.iterdir() if f.is_file()]

@mcp.resource("docs://documents/{doc_id}")
def get_document_content(doc_id: str) -> str:
    """Return the content of a specific document (for the @ mention system)."""
    return read_doc(doc_id)

@mcp.prompt()
def summarize(doc_id: str) -> str:
    """Create a prompt to summarize a specific document."""
    content = read_doc(doc_id)
    return f"Please summarize the following document:\n\nContent:\n{content}"

@mcp.prompt()
def rewrite(doc_id: str) -> str:
    """Create a prompt to rewrite a document in markdown."""
    content = read_doc(doc_id)
    return f"Please rewrite the following document in Markdown format:\n\nContent:\n{content}"

if __name__ == "__main__":
    mcp.run(transport="stdio")