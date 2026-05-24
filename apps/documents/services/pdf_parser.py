from unstructured.partition.pdf import partition_pdf
from langchain_qdrant import QdrantVectorStore
import os
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import shutil
import pdfplumber
from langchain_core.documents import Document # Import added here
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL: str = str(os.getenv("EMBEDDING_MODEL"))
STORAGE_PATH: str = str(os.getenv("STORAGE_PATH"))
COLLECTION_NAME: str = str(os.getenv("COLLECTION_NAME"))

class PDFUploadingPipeline():
  def __init__(self, file_path: str):

    documents = self.__parse_pdf(file_path)
    if documents == False:
      return
    self.__save_in_vectorstore(documents)


  def __pdf_is_chaotic(self, file_path):
    with pdfplumber.open(file_path) as pdf:
        total_paginas = len(pdf.pages)
        paginas_com_texto = 0

        for page in pdf.pages:
            # Tenta extrair texto da página
            texto = page.extract_text()
            if texto and len(texto.strip()) > 50:  # Tem pelo menos 50 caracteres
                paginas_com_texto += 1

        # Se menos de 50% das páginas tiverem texto legível, é um scan/caótico
        proporcao_texto = paginas_com_texto / total_paginas
        return proporcao_texto < 0.5


  def __parse_pdf(self, file_path):

    if self.__pdf_is_chaotic(file_path):
      # TODO: Aplicar pipeline com Azure Document Intelligence/Llhama Parsen
      print("O documento não é estruturado ou é escaneado. Recomenda-se usar um documento mais estruturado")
      return False

    elements = partition_pdf(
        filename=file_path,
        strategy="hi_res",
        infer_bounding_boxes=True,
        extract_images_in_pdf=False,
        extract_images_blocks=False,
        chunking_strategy="by_title",
        languages=["por"]
    )

    langchain_documents = []
    for element in elements:
        metadata = element.metadata.to_dict() if hasattr(element.metadata, 'to_dict') else {}
        langchain_documents.append(Document(page_content=element.text, metadata=metadata))

    return langchain_documents # Explicitly return the processed documents


  def __save_in_vectorstore(self, documents): # Corrected indentation
      embeddings_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}, # Use 'cuda' se tiver GPU
        encode_kwargs={'normalize_embeddings': True} # O BGE-M3
      )

      if os.path.exists(STORAGE_PATH):
        shutil.rmtree(STORAGE_PATH)

      self.vectorstore = QdrantVectorStore.from_documents(
        documents=documents,
        embedding=embeddings_model,
        path=STORAGE_PATH, # Pass the path directly to from_documents for local storage
        collection_name=COLLECTION_NAME,
      )
