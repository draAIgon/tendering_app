from agents.document_extraction import DocumentExtractionAgent


class BiddingAnalysisSystem:

    def __init__(self):
        self.document_extractor = DocumentExtractionAgent()
        # self.classifier = DocumentClassificationAgent()
        # self.validator = ComplianceValidationAgent()
        # self.comparator = ProposalComparisonAgent()
        # self.risk_analyzer = RiskAnalysisAgent()
        # self.reporter = ReportGenerationAgent()

    def analyze_document(self, document):
        self.document_extractor.document = document
        extracted_data = self.document_extractor.process_document()
        # TODO: Agregar el procesamiento con otros agentes
        return extracted_data