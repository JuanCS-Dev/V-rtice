#!/bin/bash

###############################################################################
# Script de Renomeação: Maximus -> Maximus
#
# Este script renomeia todas as ocorrências de "Maximus" para "Maximus"
# em todo o projeto vertice-terminal
#
# Uso: bash rename_maximus_to_maximus.sh
###############################################################################

echo "🔄 Iniciando renomeação Maximus -> Maximus..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="/home/juan/vertice-dev/vertice-terminal"

# Função para substituir em arquivos
replace_in_files() {
    local pattern=$1
    local replacement=$2
    local file_pattern=$3

    echo -e "${CYAN}Substituindo '$pattern' por '$replacement' em arquivos $file_pattern${NC}"

    find "$BASE_DIR" -type f -name "$file_pattern" \
        ! -path "*/node_modules/*" \
        ! -path "*/.git/*" \
        ! -path "*/venv/*" \
        ! -path "*/__pycache__/*" \
        ! -path "*/dist/*" \
        -exec sed -i "s/$pattern/$replacement/g" {} +
}

# Função para renomear arquivos e diretórios
rename_files_and_dirs() {
    echo -e "${CYAN}Renomeando arquivos e diretórios...${NC}"

    # Renomeia arquivos primeiro
    find "$BASE_DIR" -depth -type f -name "*maximus*" \
        ! -path "*/node_modules/*" \
        ! -path "*/.git/*" \
        ! -path "*/venv/*" \
        ! -path "*/__pycache__/*" | while read -r file; do
        new_name=$(echo "$file" | sed 's/maximus/maximus/g')
        if [ "$file" != "$new_name" ]; then
            echo -e "${GREEN}  Renomeando arquivo: $(basename "$file") -> $(basename "$new_name")${NC}"
            mv "$file" "$new_name"
        fi
    done

    # Depois renomeia diretórios
    find "$BASE_DIR" -depth -type d -name "*maximus*" \
        ! -path "*/node_modules/*" \
        ! -path "*/.git/*" \
        ! -path "*/venv/*" | while read -r dir; do
        new_name=$(echo "$dir" | sed 's/maximus/maximus/g')
        if [ "$dir" != "$new_name" ]; then
            echo -e "${GREEN}  Renomeando diretório: $(basename "$dir") -> $(basename "$new_name")${NC}"
            mv "$dir" "$new_name"
        fi
    done
}

echo -e "${YELLOW}=== SUBSTITUIÇÕES EM ARQUIVOS ===${NC}"
echo ""

# Substituições case-sensitive
replace_in_files "Maximus" "Maximus" "*.py"
replace_in_files "maximus" "maximus" "*.py"
replace_in_files "AURORA" "MAXIMUS" "*.py"

replace_in_files "Maximus" "Maximus" "*.md"
replace_in_files "maximus" "maximus" "*.md"
replace_in_files "AURORA" "MAXIMUS" "*.md"

replace_in_files "Maximus" "Maximus" "*.yaml"
replace_in_files "maximus" "maximus" "*.yaml"
replace_in_files "AURORA" "MAXIMUS" "*.yaml"

replace_in_files "Maximus" "Maximus" "*.yml"
replace_in_files "maximus" "maximus" "*.yml"
replace_in_files "AURORA" "MAXIMUS" "*.yml"

replace_in_files "Maximus" "Maximus" "*.json"
replace_in_files "maximus" "maximus" "*.json"

replace_in_files "Maximus" "Maximus" "*.txt"
replace_in_files "maximus" "maximus" "*.txt"

replace_in_files "Maximus" "Maximus" "*.sh"
replace_in_files "maximus" "maximus" "*.sh"

echo ""
echo -e "${YELLOW}=== RENOMEANDO ARQUIVOS E DIRETÓRIOS ===${NC}"
echo ""

rename_files_and_dirs

echo ""
echo -e "${YELLOW}=== ATUALIZAÇÕES ESPECÍFICAS ===${NC}"
echo ""

# Atualiza imports em Python
echo -e "${CYAN}Atualizando imports Python...${NC}"
find "$BASE_DIR" -type f -name "*.py" \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    ! -path "*/venv/*" \
    ! -path "*/__pycache__/*" \
    -exec sed -i 's/from \.\.connectors\.maximus/from ..connectors.maximus/g' {} +

find "$BASE_DIR" -type f -name "*.py" \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    ! -path "*/venv/*" \
    ! -path "*/__pycache__/*" \
    -exec sed -i 's/from \.\.connectors\.ai_agent/from ..connectors.maximus_agent/g' {} +

# Atualiza referências em YAML
echo -e "${CYAN}Atualizando referências em arquivos de configuração...${NC}"
find "$BASE_DIR" -type f \( -name "*.yaml" -o -name "*.yml" \) \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    -exec sed -i 's/maximus_orchestrator/maximus_orchestrator/g' {} +

find "$BASE_DIR" -type f \( -name "*.yaml" -o -name "*.yml" \) \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    -exec sed -i 's/ai_agent_service/maximus_service/g' {} +

echo ""
echo -e "${GREEN}✅ Renomeação concluída!${NC}"
echo ""
echo -e "${YELLOW}Próximos passos:${NC}"
echo "1. Revise as mudanças: git diff"
echo "2. Teste os comandos: python -m vertice.cli maximus --help"
echo "3. Execute os testes se houver"
echo "4. Commit as mudanças: git add . && git commit -m 'refactor: Renomear Maximus para Maximus'"
echo ""
echo -e "${CYAN}Arquivos modificados podem ser visualizados com: git status${NC}"
