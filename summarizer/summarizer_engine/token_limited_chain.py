import tiktoken
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

class TokenLimitedChain:
    """
    A chain that limits the token count to prevent exceeding API limits.
    """
    def __init__(self, llm, max_tokens=120000): 
        self.llm = llm
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text

        first_part_tokens = tokens[:max_tokens // 2]
        last_part_tokens = tokens[-max_tokens // 2:]
        
        truncated_text = (
            self.encoding.decode(first_part_tokens) + 
            "\n\n[... CONTENT TRUNCATED ...]\n\n" + 
            self.encoding.decode(last_part_tokens)
        )
        
        return truncated_text
    
    def run(self, system: str, prompt: str) -> str:
        """Run the chain with token limiting."""
        system_tokens = len(self.encoding.encode(system))
        prompt_tokens = len(self.encoding.encode(prompt))

        total_tokens = system_tokens + prompt_tokens

        if total_tokens > self.max_tokens:
            available_tokens = self.max_tokens

            system_limit = int(available_tokens * (system_tokens / total_tokens))
            prompt_limit = available_tokens - system_limit
            
            system = self._truncate_text(system, system_limit)
            prompt = self._truncate_text(prompt, prompt_limit)

        chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template="{system}\n\n{prompt}",
                input_variables=["system", "prompt"]
            )
        )

        return chain.run(system=system, prompt=prompt)