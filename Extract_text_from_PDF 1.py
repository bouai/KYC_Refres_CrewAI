import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
import tempfile
from pathlib import Path

os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"] = "https://azuredocintelli-poc.cognitiveservices.azure.com/"
os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"] = "AZURE_OPENAI_KEY"

def extract_data_from_pdf(pdf_path, output_folder="extracted_data"):
    """
    Extract data from both searchable and scanned PDF files using Azure AI Document Intelligence
    
    Args:
        pdf_path: Path to the PDF file
        output_folder: Folder to save extracted text
        
    Returns:
        Dictionary containing the extracted content and analysis results
    """
    # Create output directory if it doesn't exist
    Path(output_folder).mkdir(exist_ok=True)
    
    # Azure Document Intelligence settings
    endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    
    if not endpoint or not key:
        raise ValueError("Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY environment variables")
    
    # Initialize client
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, 
        credential=AzureKeyCredential(key)
    )
    
    print(f"Processing PDF: {pdf_path}")
    
    # Read the document
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    # Create analyze request - using the prebuilt-read model
    # Pass the document bytes directly
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-read",  # Changed model ID
        document_bytes
    )
    
    result = poller.result()
    
    # Save extracted content
    file_name = os.path.basename(pdf_path).split('.')[0]
    output_text_path = os.path.join(output_folder, f"{file_name}_extracted_text.txt")
    #output_json_path = os.path.join(output_folder, f"{file_name}_analysis.json")
    
    # Extract and save text content
    content = result.content
    with open(output_text_path, "w", encoding="utf-8") as text_file:
        text_file.write(content)
    
    # Extract structured information
    extracted_data = {
        'content': content,
        'tables': [],
        'key_value_pairs': [],
        'paragraphs': []
    }
    
    # Extract tables if available
    if result.tables:
        for i, table in enumerate(result.tables):
            table_data = []
            for cell in table.cells:
                row_idx = cell.row_index
                col_idx = cell.column_index
                # Ensure the table is large enough
                while len(table_data) <= row_idx:
                    table_data.append([])
                row = table_data[row_idx]
                while len(row) <= col_idx:
                    row.append("")
                row[col_idx] = cell.content
            
            extracted_data['tables'].append(table_data)
    
    # Extract key-value pairs if available
    if result.key_value_pairs:
        for kv in result.key_value_pairs:
            if kv.key and kv.value:
                key = kv.key.content if kv.key.content else ""
                value = kv.value.content if kv.value.content else ""
                if key and value:
                    extracted_data['key_value_pairs'].append({
                        'key': key,
                        'value': value
                    })
    
    # Extract paragraphs
    if result.paragraphs:
        for para in result.paragraphs:
            extracted_data['paragraphs'].append(para.content)
    
    print(f"Document processing complete. Output saved to {output_text_path}")
    return extracted_data

# Example usage
def process_multiple_pdfs(pdf_folder, output_folder="extracted_data"):
    """Process multiple PDFs from a folder"""
    results = {}
    for file in os.listdir(pdf_folder):
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder, file)
            print(f"Processing: {file}")
            results[file] = extract_data_from_pdf(pdf_path, output_folder)
    return results

# # Only run example usage if the script is executed directly
# if __name__ == "__main__":
#     # process multiple PDFs in a folder
#     results = process_multiple_pdfs("Data")
#     print("\nExample Usage Results:")
#     # Optionally print summary of results
#     for filename, data in results.items():
#         print(f"  {filename}: Extracted {len(data.get('content', ''))} characters.")

