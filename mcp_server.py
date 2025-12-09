from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Read the contents of a document by its ID."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    return docs[doc_id]

@mcp.tool()
def edit_doc(doc_id: str, content: str) -> str:
    """Edit the contents of a document."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    docs[doc_id] = content
    return f"Successfully updated {doc_id}"

@mcp.resource("docs://documents")
def list_documents() -> list[str]:
    """Return a list of all document IDs."""
    return list(docs.keys())

@mcp.resource("docs://documents/{doc_id}")
def get_document_content(doc_id: str) -> str:
    """Return the content of a specific document."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    return docs[doc_id]

@mcp.prompt()
def summarize(doc_id: str) -> str:
    """Create a prompt to summarize a specific document."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    
    content = docs[doc_id]
    return f"Please summarize the following document:\n\nContent:\n{content}"

@mcp.prompt()
def rewrite(doc_id: str) -> str:
    """Create a prompt to rewrite a document in markdown."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    
    content = docs[doc_id]
    return f"Please rewrite the following document in Markdown format:\n\nContent:\n{content}"


if __name__ == "__main__":
    mcp.run(transport="stdio")