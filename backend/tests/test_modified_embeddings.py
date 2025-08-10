import sys
import os
sys.path.append('./backend')

from utils.embedding import build_embeddings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print('🔬 Probando SISTEMA MODIFICADO de embeddings simplificado')
print('=' * 60)

try:
    # Probar con archivos disponibles
    db = build_embeddings(
        carpeta_lawdata='./LawData',
        ruta_db='./db/chroma/test_modified',
        collection_name='test_modified',
        provider='auto',
        chunk_size=2000,
        chunk_overlap=1000,
        reset_db=True
    )

    if db:
        print('')
        print('✅ Base de datos creada exitosamente con sistema modificado')
        print('')
        
        # Probar búsquedas usando la base de datos directamente
        test_queries = ['requisitos técnicos', 'garantías', 'objeto del contrato', 'cronograma']
        
        for query in test_queries:
            print(f"{'='*40}")
            print(f"🔍 Búsqueda: '{query}'")
            
            try:
                results = db.similarity_search(query, k=3)
                print(f"📋 Encontrados {len(results)} resultados:")
                
                for i, doc in enumerate(results, 1):
                    source = doc.metadata.get('source', 'unknown')
                    section = doc.metadata.get('section', 'unknown')
                    page = doc.metadata.get('page', 'N/A')
                    
                    preview = doc.page_content[:150].replace('\n', ' ').strip()
                    
                    print(f"   {i}. {source} (sección: {section})")
                    print(f"      Vista previa: {preview}...")
                    print("")
            except Exception as e:
                print(f"   ❌ Error en búsqueda: {e}")
            
            print('')
    else:
        print('❌ Error creando base de datos')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
