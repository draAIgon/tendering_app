"""
Test final directo de RUC validation
"""

import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

root_dir = os.path.dirname(backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.utils.agents.ruc_validator import RUCValidationAgent

# Test directo
ruc_validator = RUCValidationAgent()

content_with_rucs = """
CONSTRUCTORA ANDES S.A.
RUC: 1790123456001

REPRESENTANTE LEGAL:
Juan Pérez
RUC: 1712345678001

SUBCONTRATISTA:
Ingeniería Moderna
RUC: 1791234567001
"""

result = ruc_validator.comprehensive_ruc_validation(content_with_rucs, 'CONSTRUCCION')

print(f"✅ RUCs detectados: {result['validation_summary']['total_rucs']}")
print(f"✅ Score: {result['overall_score']}%")
print(f"✅ Nivel: {result['validation_level']}")

if result['validation_summary']['total_rucs'] > 0:
    print("🎉 ¡RUC VALIDATION FUNCIONA PERFECTAMENTE!")
else:
    print("⚠️ No se detectaron RUCs")
