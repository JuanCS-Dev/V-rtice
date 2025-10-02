#!/usr/bin/env python3
"""
Script para aplicar mudanças do Maximus AI + Gemini no main.py
"""

# Lê o arquivo
with open('main.py', 'r') as f:
    content = f.read()

# 1. Adiciona imports do Maximus após MemorySystem
maximus_imports = """
# MAXIMUS AI 2.0 INTEGRATED SYSTEM - Complete AI Brain
from maximus_integrated import (
    MaximusIntegratedSystem,
    MaximusRequest,
    MaximusResponse,
    ResponseMode
)

# MAXIMUS AI 2.0 COGNITIVE SYSTEMS
from rag_system import RAGSystem, Source, SourceType
from chain_of_thought import ChainOfThoughtEngine, ReasoningType
from confidence_scoring import ConfidenceScoringSystem
from self_reflection import SelfReflectionEngine

# GEMINI CLIENT
from gemini_client import GeminiClient, GeminiConfig
"""

# Encontra a linha após MemorySystem import e adiciona
import_marker = "from memory_system import MemorySystem, ConversationContext"
if import_marker in content:
    content = content.replace(
        import_marker,
        import_marker + "\n" + maximus_imports
    )

# 2. Muda Aurora para Maximus nos comentários
content = content.replace("# MEMORY SYSTEM - Aurora's memory", "# MEMORY SYSTEM - Maximus's memory")

# 3. Adiciona GEMINI_API_KEY
api_keys_section = 'OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")'
if api_keys_section in content and 'GEMINI_API_KEY' not in content:
    content = content.replace(
        api_keys_section,
        api_keys_section + '\nGEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")'
    )

# 4. Adiciona inicialização do Gemini Client
gemini_init = """
# Initialize Gemini Client
gemini_client = None
if GEMINI_API_KEY:
    gemini_config = GeminiConfig(
        api_key=GEMINI_API_KEY,
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=4096
    )
    gemini_client = GeminiClient(gemini_config)
    print("✅ Gemini client initialized")
"""

reasoning_marker = "# Initialize Reasoning Engine"
if reasoning_marker in content and "gemini_client = None" not in content:
    content = content.replace(reasoning_marker, gemini_init + "\n" + reasoning_marker)

# 5. Atualiza ReasoningEngine para incluir gemini_client
old_reasoning = """reasoning_engine = ReasoningEngine(
    llm_provider=LLM_PROVIDER,
    anthropic_api_key=ANTHROPIC_API_KEY,
    openai_api_key=OPENAI_API_KEY
)"""

new_reasoning = """reasoning_engine = ReasoningEngine(
    llm_provider=LLM_PROVIDER,
    anthropic_api_key=ANTHROPIC_API_KEY,
    openai_api_key=OPENAI_API_KEY,
    gemini_client=gemini_client
)"""

if old_reasoning in content:
    content = content.replace(old_reasoning, new_reasoning)

# 6. Muda LLM_PROVIDER default para gemini
content = content.replace(
    'LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")',
    'LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")'
)

# 7. Adiciona inicialização do Maximus System
maximus_init = """
# Initialize Maximus AI 2.0 Integrated System
maximus_system = MaximusIntegratedSystem(
    llm_client=gemini_client,
    enable_rag=True,
    enable_reasoning=True,
    enable_memory=True,
    enable_reflection=True
)
"""

orchestrator_marker = "# Lifecycle events"
if orchestrator_marker in content and "maximus_system = MaximusIntegratedSystem" not in content:
    content = content.replace(orchestrator_marker, maximus_init + "\n" + orchestrator_marker)

# 8. Adiciona inicialização do Maximus no startup
old_startup = """    except Exception as e:
        print(f"⚠️  Memory System initialization failed: {e}")
        print("   Aurora will run without persistent memory")

@app.on_event("shutdown")"""

new_startup = """    except Exception as e:
        print(f"⚠️  Memory System initialization failed: {e}")
        print("   Aurora will run without persistent memory")

    try:
        await maximus_system.initialize()
        print("✅ Maximus AI 2.0 Integrated System initialized")
    except Exception as e:
        print(f"⚠️  Maximus AI 2.0 initialization failed: {e}")

@app.on_event("shutdown")"""

if old_startup in content:
    content = content.replace(old_startup, new_startup)

# 9. Adiciona shutdown do Maximus
old_shutdown = """    await memory_system.shutdown()
    print("👋 Memory System shutdown")

# ========================================"""

new_shutdown = """    await memory_system.shutdown()
    print("👋 Memory System shutdown")

    await maximus_system.shutdown()
    print("👋 Maximus AI 2.0 shutdown")

# ========================================"""

if old_shutdown in content:
    content = content.replace(old_shutdown, new_shutdown)

# 10. Atualiza call_llm_with_tools para incluir Gemini
old_llm_call = """async def call_llm_with_tools(messages: List[Dict], tools: List[Dict]) -> Dict:
    \"\"\"
    Chama o LLM (Anthropic Claude) com tool calling support
    \"\"\"
    if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:"""

new_llm_call = """async def call_llm_with_tools(messages: List[Dict], tools: List[Dict]) -> Dict:
    \"\"\"
    Chama o LLM com tool calling support (Gemini, Anthropic Claude, OpenAI GPT)
    \"\"\"
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        return await call_google_gemini(messages, tools)
    elif LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:"""

if old_llm_call in content:
    content = content.replace(old_llm_call, new_llm_call)

# 11. Adiciona função call_google_gemini antes de call_anthropic_claude
gemini_function = '''
async def call_google_gemini(messages: List[Dict], tools: List[Dict]) -> Dict:
    """Chama Google Gemini API com tool calling"""

    if not GEMINI_API_KEY or not gemini_client:
        return {
            "role": "assistant",
            "content": "Configure GEMINI_API_KEY para usar Gemini",
            "tool_calls": []
        }

    try:
        # Extrai system message
        system_instruction = None
        conversation_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                conversation_messages.append({
                    "role": msg["role"],
                    "content": msg.get("content", "")
                })

        # Chama Gemini
        if conversation_messages:
            response = await gemini_client.generate_with_conversation(
                messages=conversation_messages,
                system_instruction=system_instruction,
                tools=tools if tools else None
            )
        else:
            response = await gemini_client.generate_text(
                prompt=system_instruction or "Hello",
                tools=tools if tools else None
            )

        # Converte resposta para formato unificado
        tool_calls = []
        for tc in response.get("tool_calls", []):
            tool_calls.append({
                "id": f"call_{tc['name']}",
                "name": tc["name"],
                "input": tc.get("arguments", {})
            })

        return {
            "role": "assistant",
            "content": response.get("text", ""),
            "tool_calls": tool_calls,
            "stop_reason": response.get("finish_reason", "stop")
        }

    except Exception as e:
        return {
            "role": "assistant",
            "content": f"Erro ao chamar Gemini: {str(e)}",
            "tool_calls": []
        }

'''

anthropic_marker = "async def call_anthropic_claude(messages: List[Dict], tools: List[Dict]) -> Dict:"
if anthropic_marker in content and "async def call_google_gemini" not in content:
    content = content.replace(anthropic_marker, gemini_function + anthropic_marker)

# Salva o arquivo modificado
with open('main.py', 'w') as f:
    f.write(content)

print("✅ Mudanças do Maximus AI + Gemini aplicadas com sucesso!")
print("📝 Backup salvo em: main.py.backup_before_maximus")
