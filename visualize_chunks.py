"""
Script para mostrar cómo el sistema simplificado está dividiendo los chunks
del documento, similar al ejemplo estructurado que se mostró
"""

import sys
sys.path.append('./backend')

from utils.embedding import build_embeddings
import logging

# Configurar logging más silencioso para focus en los chunks
logging.basicConfig(level=logging.WARNING)

print('🔍 VISUALIZACIÓN DE CHUNKS - Sistema Simplificado')
print('=' * 80)

try:
    # Crear base de datos con sistema simplificado
    db = build_embeddings(
        carpeta_lawdata='./LawData',
        ruta_db='./db/chroma/chunk_visualization',
        collection_name='chunk_viz',
        provider='auto',
        chunk_size=2000,
        chunk_overlap=1000,
        reset_db=True
    )

    if db:
        print('\n✅ Base de datos creada. Mostrando división de chunks:\n')
        
        # Obtener todos los documentos para ver cómo están divididos
        collection = db._collection
        all_docs = collection.get(include=['documents', 'metadatas'])
        
        if all_docs['documents']:
            # Agrupar por source y ordenar por chunk_id si existe
            chunks_by_source = {}
            
            for i, (doc, metadata) in enumerate(zip(all_docs['documents'], all_docs['metadatas'])):
                source = metadata.get('source', 'unknown')
                if source not in chunks_by_source:
                    chunks_by_source[source] = []
                
                chunks_by_source[source].append({
                    'index': i,
                    'content': doc,
                    'metadata': metadata,
                    'length': len(doc)
                })
            
            # Mostrar chunks para cada documento
            for source, chunks in chunks_by_source.items():
                print(f"\n{'='*80}")
                print(f"📄 DOCUMENTO: {source}")
                print(f"📊 Total de chunks: {len(chunks)}")
                print('='*80)
                
                for j, chunk in enumerate(chunks[:10]):  # Mostrar primeros 10 chunks
                    section = chunk['metadata'].get('section', 'GENERAL')
                    page = chunk['metadata'].get('page', 'N/A')
                    length = chunk['length']
                    
                    print(f"\n🔹 CHUNK #{j+1}")
                    print(f"   📍 Sección: {section}")
                    print(f"   📄 Página: {page}")
                    print(f"   📏 Longitud: {length} caracteres")
                    print(f"   {'='*60}")
                    
                    # Mostrar contenido del chunk
                    content = chunk['content']
                    
                    # Mostrar las primeras líneas para ver la estructura
                    lines = content.split('\n')[:15]  # Primeras 15 líneas
                    for line in lines:
                        if line.strip():
                            print(f"   {line}")
                    
                    if len(content.split('\n')) > 15:
                        print(f"   ... (continúa por {len(content.split('\n')) - 15} líneas más)")
                    
                    print(f"   {'='*60}")
                    
                    # Separador entre chunks
                    print()
                
                if len(chunks) > 10:
                    print(f"\n   📝 ... y {len(chunks) - 10} chunks adicionales")
        
        # Ahora mostrar algunas búsquedas para ver la recuperación
        print(f"\n{'='*80}")
        print("🔍 PRUEBAS DE BÚSQUEDA SEMÁNTICA")
        print('='*80)
        
        test_queries = [
            "PRIMERA – OBJETO DEL CONTRATO", 
            "garantías",
            "cronograma de ejecución",
            "ANEXO"
        ]
        
        for query in test_queries:
            print(f"\n🔎 Búsqueda: '{query}'")
            print('-' * 50)
            
            results = db.similarity_search(query, k=3)
            
            for i, result in enumerate(results, 1):
                source = result.metadata.get('source', 'unknown')
                section = result.metadata.get('section', 'unknown')
                
                # Mostrar snippet del contenido encontrado
                content_lines = result.page_content.split('\n')[:5]
                preview = '\n   '.join([line for line in content_lines if line.strip()])
                
                print(f"   {i}. 📄 {source} (📍 {section})")
                print(f"      {preview[:200]}...")
                print()
    
    else:
        print('❌ Error creando base de datos')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
