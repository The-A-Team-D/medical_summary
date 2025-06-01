import os
import tempfile
import json
import pikepdf
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from typing import List, Dict, Tuple

from .token_limited_chain import TokenLimitedChain
from .feedback_learner import FeedbackLearner

class MedicalSummarizer:
    def __init__(self, config, new_pdf, example_without_password=None):
        self.config = config
        self.example_without_password = example_without_password or []
        self.new_pdf = new_pdf
        self.embeddings = OpenAIEmbeddings(openai_api_key=config["openai_api_key"])
        self.llm = ChatOpenAI(
            model_name=config["model_name"],
            openai_api_key=config["openai_api_key"],
            temperature=0.3 
        )
        self.example_data = []
        self.vector_store = None
        self.feedback_learner = FeedbackLearner(feedback_directory=config.get("feedback_dir", "./feedback"))
        
    def extract_pdf_text(self, pdf_path, password=None):
        try:
            temp_file = None

            if password:
                temp_fd, temp_path = tempfile.mkstemp(dir=self.config["temp_dir"], suffix='.pdf')
                os.close(temp_fd) 
                
                with pikepdf.open(pdf_path, password=password) as pdf:
                    pdf.save(temp_path)
                
                pdf_path_to_load = temp_path
                temp_file = temp_path
            else:
                pdf_path_to_load = pdf_path

            loader = PyPDFLoader(pdf_path_to_load)
            documents = loader.load()

            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

            text = "\n\n--- Page Break ---\n\n".join([doc.page_content for doc in documents])
            return text
            
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            return None

    
    def load_example_data(self):
        examples = []
        for example in self.config.get("examples", []):
            extracted_text = self.extract_pdf_text(example["pdf"], self.config.get("pdf_password"))
            
            if extracted_text:
                with open(example["summary"], 'r') as f:
                    summary_text = f.read()
                
                examples.append({
                    "extracted_text": extracted_text,
                    "summary": summary_text
                })

        for example in self.example_without_password:
            extracted_text = self.extract_pdf_text(example["pdf"])
            
            if extracted_text:
                with open(example["summary"], 'r') as f:
                    summary_text = f.read()
                
                examples.append({
                    "extracted_text": extracted_text,
                    "summary": summary_text
                })
        
        self.example_data = examples
    
    def create_vector_store(self):
        if not self.config.get("use_vectorstore_for_selection", False):
            return
            
        from langchain.vectorstores import FAISS
        documents = []
        metadatas = []
        
        for i, example in enumerate(self.example_data):
            documents.append(example["extracted_text"])
            metadatas.append({"summary": example["summary"], "index": i})
        
        self.vector_store = FAISS.from_texts(
            documents, 
            self.embeddings, 
            metadatas=metadatas
        )
    
    def get_similar_examples(self, new_text, k=3):
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call create_vector_store() first.")
        
        similar_docs = self.vector_store.similarity_search(new_text, k=k)
        
        examples = []
        for doc in similar_docs:
            examples.append({
                "content": doc.page_content,
                "summary": doc.metadata["summary"]
            })
        
        return examples
    
    def create_pattern_summary_system_prompt(self):
        summaries = [example["summary"] for example in self.example_data] 

        system_prompt = """
        You are a specialized medical document summarizer that creates summaries for emergency room visit documents.
        
        Based on the examples provided, create a summary with the exact same structure, format, and level of detail.
        Pay careful attention to:
        1. The sections included in each summary (chief complaints, diagnoses, lab results, etc.)
        2. The order of information presentation
        3. The style of writing (concise, factual, professional)
        4. Any specific formatting patterns (bullet points, section headers, etc.)
        5. The types of medical details that are considered relevant enough to include
        
        Your goal is to create a summary for what made patient come to emergency room visit document. Make sure pain level will be more than 5 always, as this is emergency room visit. Also do not mention reason for emergency room visit as 'influenza-like illness', as this is not the critical reason.
        """
        
        # # Add any adaptive prompting from feedback
        # self.feedback_learner.scan_for_new_corrections()
        # improvement_prompt = self.feedback_learner.get_improvement_prompt()
        # system_prompt += improvement_prompt
        
        return system_prompt
    
    def create_prompt_with_examples(self, new_text):
        examples_to_include = []
        
        if self.config.get("use_few_shot_selection", False) and self.config.get("use_vectorstore_for_selection", False):
            examples_to_include = self.get_similar_examples(
                new_text, 
                k=min(self.config.get("max_examples_to_include", 5), len(self.example_data))
            )
        else:
            max_examples = min(self.config.get("max_examples_to_include", 5), len(self.example_data))
            examples_to_include = [
                {"content": example["extracted_text"], "summary": example["summary"]} 
                for example in self.example_data[:max_examples]
            ]

        if self.config.get("use_fewshot_examples", True):
            prompt_template = """
                I want you to analyze the provided examples and generate an emergency room visit summary for a new patient document that follows the EXACT format demonstrated below:

                {examples}

                Now, create a summary for this new document that STRICTLY follows the same format:
                [NEW CONTENT START]
                {new_content}
                [NEW CONTENT END]

                OUTPUT FORMAT SPECIFICATION:
                You MUST format your output as a single section titled "Patient Acuity and Complexity:" followed by three distinct paragraphs:

                Paragraph 1: Specify the patient's acuity level (level 4 acuity, 99284 or level 5 acuity, 99285) and include the definition: "which is defined as: emergency department visit for the evaluation and management of a patient, which requires a medically appropriate history and/or examination and moderate level of medical decision making."

                Paragraph 2: Describe why the patient came to the Emergency Room, in the following PRECISE order:
                - Age and presenting complaints (MUST include ALL symptoms including chest pain if mentioned)
                - CRITICAL: List ALL medical history conditions in the FIRST SENTENCE before mentioning pain level (e.g., "The patient with a history of Hypertension, Diabetes Mellitus, Depression, etc."), even if past medical history or surgical history does not exist then do not need to write "The patient has no significant past medical history or surgical history."
                - ALL surgical history (e.g., Bilateral Ear Tubes, Cholecystectomy, Tonsillectomy, etc.) must be included
                - Pain level (MUST be at least 6/10)
                - ALL physical examination findings (especially nasal conditions, discharge, injection)
                - Duration and history of symptoms 
                - Reason for urgency/emergency room visit (use EXACT language from source document)
                - When the patient arrived
                - Patient's concerns about delaying treatment

                Paragraph 3: Describe the provider's actions and findings, including:
                - Provider's experience and approach
                - Differential diagnoses considered (list ALL possibilities including conditions like Abortion)
                - Laboratory tests ordered and results (including ALL cultures)
                - ALL diagnostic procedures performed (especially EKG with exact findings like "abnormal finding - The rhythm was sinus with PVC's")
                - ALL medications administered (including full details like "Dexamethasone sod (Decadron) 10mg/ml INJ -10mg IVPB")
                - ALL hydration provided (e.g., "SOD CHL, IVSOL 0.9% 100ML")
                - Final diagnosis
                - Discharge plan and prescriptions (ALL medications mentioned, including eye drops like "Vigamox 0.5% Eye Drops")

                CRITICAL CONTENT REQUIREMENTS:
                1. Include ALL positive AND negative physical examination findings
                2. Include EVERY medication mentioned in the source document (both administered and prescribed)
                3. Include EVERY condition listed in the medical history (including ADHD, depression, anxiety, etc.)
                4. Include EVERY surgical history item mentioned
                5. Include "Suspected exposure" information
                6. Report pain level as greater than 5/10 in all cases (minimum 6/10)
                7. Use accurate calendar dates with correct day of week calculation
                8. When mentioning diabetes, use "diabetes mellitus" without specifying "non-insulin dependent"
                9. Focus on acute, serious presentations rather than mild conditions
                10. NEVER use "influenza-like illness," "body ache," or "cough" as primary reasons for the visit
                11. Always describe the EXACT reason for visit using the patient's own concerns or language
                12. Always list medical history conditions BEFORE discussing pain levels
                13. If constipation is mentioned, include it as a symptom

                SPECIFIC FORMATTING RULES:
                1. Write numbers of days alphabetically (e.g., "two days" instead of "2 days")
                2. When listing diseases, DO NOT include symptoms except for dehydration
                3. Capitalize the first letter of each condition in the medical history
                4. NEVER use abbreviations - always write out full terms

                VERIFICATION CHECKLIST:
                Before submitting your response, verify that:
                1. Your output has a single heading: "Patient Acuity and Complexity:"
                2. Your output contains exactly three paragraphs in the specified format
                3. The first paragraph specifies the correct acuity level with the exact definition
                4. The second paragraph contains all required patient information with medical history conditions FIRST
                5. ALL symptoms are included
                6. ALL surgical history is included
                7. ALL physical examination findings are included
                8. The third paragraph contains ALL provider actions and findings
                9. ALL medications administered and prescribed are included with full details
                10. ALL diagnostic tests and results are included
                11. ALL differential diagnoses are included
                12. All pain levels are at least 6/10
                13. All dates are calendar-accurate with correctly calculated days of the week
                14. All numbers for days are written alphabetically
                15. No abbreviations are used - all terms are written in full
                16. All required content from the source document is included

                MOST IMPORTANT: Your output MUST match the format of the example I provided. DO NOT create additional sections or headings. Keep everything under the single "Patient Acuity and Complexity:" heading with three paragraphs as shown.
            """
            
            examples_text = ""
            for i, example in enumerate(examples_to_include):
                examples_text += f"Example document {i+1} has this content:\n\n"
                examples_text += f"[CONTENT START]\n{example['content']}\n[CONTENT END]\n\n"
                examples_text += f"And its summary is:\n\n"
                examples_text += f"[SUMMARY START]\n{example['summary']}\n[SUMMARY END]\n\n"
            
            prompt = PromptTemplate(
                input_variables=["examples", "new_content"],
                template=prompt_template
            ).format(examples=examples_text, new_content=new_text)
        else:
            prompt_template = """
            Create a summary for what made patient come to emergency room visit document. Make sure pain level will be more than 5 always, as this is emergency room visit. Also do not mention reason for emergency room visit as 'influenza-like illness', as this is not the critical reason:
            
            [CONTENT START]
            {new_content}
            [CONTENT END]
            
            The summary should follow the exact format, structure, and level of detail seen in emergency room visit summaries.
            """
            
            prompt = PromptTemplate(
                input_variables=["new_content"],
                template=prompt_template
            ).format(new_content=new_text)
        
        return prompt
    
    def create_metadata_file(self, output_path="medical_summary_metadata.json"):
        metadata = []
        
        for i, example in enumerate(self.example_data):
            metadata.append({
                "id": i,
                "content": example["extracted_text"][:500] + "...",  # Truncate for readability
                "summary": example["summary"]
            })
        
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Metadata saved to {output_path}")
        return output_path
    
    def summarize(self, project_name, output_file=None):
        self.load_example_data()

        if self.config.get("create_metadata", False):
            self.create_metadata_file()
        
        if self.config.get("use_vectorstore_for_selection", False):
            self.create_vector_store()
        
        new_pdf_text = self.extract_pdf_text(
            self.new_pdf,
            self.config.get("new_pdf_password")
        )
        
        if not new_pdf_text:
            print("Failed to extract text from the new PDF. Exiting.")
            return None
        
        system_prompt = self.create_pattern_summary_system_prompt()
        prompt = self.create_prompt_with_examples(new_pdf_text)

        token_limited_chain = TokenLimitedChain(
            llm=self.llm, 
            max_tokens=128000 
        )

        result = token_limited_chain.run(system=system_prompt, prompt=prompt)
        
        # Store the original summary for potential feedback
        if output_file:
            self.feedback_learner.store_original_summary(output_file, result)
        
        return result, new_pdf_text
    
    def process_human_correction(self, original_filename, corrected_summary):
        """Process a human correction to improve future summaries"""
        error_report = self.feedback_learner.register_correction(original_filename, corrected_summary)
        print(f"Processed correction for {original_filename}")
        return error_report
    
    def generate_error_analysis_report(self):
        """Generate an error analysis report to understand common mistakes"""
        return self.feedback_learner.generate_error_analysis_report()