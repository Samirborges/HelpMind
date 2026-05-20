from pydantic import BaseModel, Field
from typing import List
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json 

class DocumentAnalysis(BaseModel):
    category: str = Field(description="Categoria principal do documento (ex: RH, TI, Jurídico)")
    summary: str = Field(description="Resumo de 2 frases sobre o conteúdo")
    tags: List[str] = Field(description="Lista de 3 a 5 palavras-chave")
    department: str = Field(description="Departamento responsável")


class PDFProcessingPipeline():
  def __init__(self, file_path: str, llm):
    self.llm = llm

    loader_analysis = UnstructuredPDFLoader(file_path, model="single")
    raw_text = loader_analysis.load()[0].page_content

    self.dynamic_info = self.__extract_metadata_with_llm(raw_text[:5000])
    self.loader = UnstructuredPDFLoader(
        file_path,
        model="elements",
        strategy="hi_res",
    )
    self.documents = self.loader.load()

  def __extract_metadata_with_llm(self, text_to_analyze: str) -> DocumentAnalysis:
    structured_lmm = self.llm.with_structured_output(DocumentAnalysis)

    prompt = f"""Analise o texto abaixo e extraia os metadados estruturados:

    {text_to_analyze}"""

    return structured_lmm.invoke(prompt)

  def __enrichment_documents(self):
    for document in self.documents:
      document.metadata.update(self.dynamic_info.dict())
      document.metadata["processed_at"] = "2024-05-22"


  def __clear_json(self, llm_response) -> DocumentAnalysis:
    try:
        if '```json' in llm_response and '```' in llm_response:
            json_str = llm_response.split('```json')[1].split('```')[0].strip()
        else:
            json_str = llm_response.strip()
        metadata_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
        print(f"Conteúdo recebido: {llm_response}")
        return DocumentAnalysis(category="Desconhecido", summary="Não foi possível extrair metadados", tags=[], department="Desconhecido")

    return DocumentAnalysis.parse_obj(metadata_json)


  def get_intelligent_chunking(self):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(self.documents) # Corrigido de self.raw_docs para self.documents

    for chunk in chunks:
      chunk.metadata.update(self.dynamic_info.dict()) # Corrigido de self.dynamic_metadata para self.dynamic_info

    return chunks